"""
evaluate.py
───────────
Main evaluation script for comparing CoT vs ToT reasoning on mathematical
datasets.

Features
────────
• Loads all datasets defined in config.DATASET_CATEGORY_MAP
• Evaluates each sample with both Chain-of-Thought (CoT) and Tree-of-Thought
  (ToT) prompting strategies
• Saves progress to a checkpoint after every single sample
• On restart, automatically resumes from the last checkpoint
• Graceful Ctrl-C handler: saves partial reports before exiting
• Auto-saves partial reports every AUTOSAVE_EVERY samples
• On completion: generates full CSV + HTML + PDF reports

Usage
─────
  # Normal run (resumes automatically if checkpoint exists)
  python evaluate.py

  # Force a fresh start (ignore existing checkpoint)
  python evaluate.py --fresh

Dependencies
────────────
  pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ── Local imports ─────────────────────────────────────────────────────────────
from config import (
    AUTOSAVE_EVERY,
    CHECKPOINT_FILE,
    DATA_FOLDER,
    DATASET_CATEGORY_MAP,
    DEVICE,
    MAX_SAMPLES_PER_CATEGORY,
    MODEL_NAME,
    RESULTS_DIR,
    RESUME_ENABLED,
    TOT_NUM_BRANCHES,
    USE_4BIT_QUANT,
    COT_MAX_NEW_TOKENS,
    TOT_MAX_NEW_TOKENS,
)
from checkpoint_manager import CheckpointManager
from report_generator import generate_all_reports

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

try:
    from tqdm import tqdm
    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False
    print("⚠️  tqdm not installed – progress bars disabled (pip install tqdm)")

# ── Globals used by the signal handler ───────────────────────────────────────
_checkpoint_mgr: Optional[CheckpointManager] = None
_start_time: float = 0.0
_graph_path: Optional[str] = None


# ─────────────────────────── argument parsing ─────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate CoT vs ToT on math datasets")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing checkpoint and start from scratch",
    )
    return parser.parse_args()


# ─────────────────────────── signal handler ───────────────────────────────────

def handle_interrupt(sig, frame) -> None:
    """Graceful Ctrl-C: save partial reports then exit cleanly."""
    print("\n\n⚠️  INTERRUPTED! Saving progress…")
    _generate_partial_reports()
    print("✅ Progress saved! Run again to resume from where you stopped.")
    sys.exit(0)


def _generate_partial_reports() -> None:
    """Generate reports from whatever checkpoint data is available."""
    if _checkpoint_mgr is None:
        return
    df = _checkpoint_mgr.checkpoint_to_dataframe()
    if df is None or (hasattr(df, "empty") and df.empty):
        print("   (No completed samples yet — nothing to report.)")
        return
    elapsed = _elapsed_str()
    generate_all_reports(df=df, runtime_str=elapsed, graph_path=_graph_path, partial=True)
    print(f"✅ Checkpoint file: {CHECKPOINT_FILE}")


def _elapsed_str() -> str:
    secs = int(time.time() - _start_time)
    return str(timedelta(seconds=secs))


# ─────────────────────────── dataset loading ──────────────────────────────────

def _find_dataset_files() -> Dict[str, str]:
    """
    Scan DATA_FOLDER for .xlsx / .csv files and map stems to full paths.
    Returns {stem: full_path}.
    """
    if not os.path.isdir(DATA_FOLDER):
        print(f"⚠️  DATA_FOLDER not found: {DATA_FOLDER}")
        print("   Please update config.py → DATA_FOLDER to point to your data directory.")
        return {}

    files: Dict[str, str] = {}
    for fname in os.listdir(DATA_FOLDER):
        stem, ext = os.path.splitext(fname)
        if ext.lower() in (".xlsx", ".csv"):
            files[stem] = os.path.join(DATA_FOLDER, fname)
    return files


def _load_dataframe(path: str):
    """Load a .xlsx or .csv into a pandas DataFrame."""
    if not _PANDAS_AVAILABLE:
        raise ImportError("pandas is required – pip install pandas openpyxl")
    if path.lower().endswith(".xlsx"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def _detect_question_col(df) -> Optional[str]:
    """Heuristically find the question/problem column (case-insensitive)."""
    targets = {"question", "problem", "input"}
    col_lower = {c.lower(): c for c in df.columns}
    for t in targets:
        if t in col_lower:
            return col_lower[t]
    # fall back to first string column
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return None


def _detect_answer_col(df) -> Optional[str]:
    """Heuristically find the answer column (case-insensitive)."""
    targets = {"answer", "solution", "output", "target", "label"}
    col_lower = {c.lower(): c for c in df.columns}
    for t in targets:
        if t in col_lower:
            return col_lower[t]
    return None


# ─────────────────────────── model loading ────────────────────────────────────

def _load_model():
    """Load the LLM with optional 4-bit quantisation."""
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as exc:
        raise ImportError(
            "transformers / torch not installed. Run: pip install -r requirements.txt"
        ) from exc

    print(f"🔄 Loading model: {MODEL_NAME} …")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

    if USE_4BIT_QUANT:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )

    model.eval()
    print(f"✅ Model loaded ({MODEL_NAME})")
    return model, tokenizer


# ─────────────────────────── inference helpers ────────────────────────────────

def _run_cot(question: str, model, tokenizer) -> Tuple[str, str]:
    """
    CoT prompt → (raw_output, extracted_answer).
    Returns ("", "") on failure.
    """
    prompt = (
        "Solve the following problem step by step.\n\n"
        f"Problem: {question}\n\n"
        "Solution:"
    )
    return _generate(prompt, model, tokenizer, max_new_tokens=COT_MAX_NEW_TOKENS)


def _run_tot(question: str, model, tokenizer) -> Tuple[str, str]:
    """
    ToT prompt → (raw_output, extracted_answer).
    Generates TOT_NUM_BRANCHES branches and selects the most common answer.
    Returns ("", "") on failure.
    """
    branch_outputs: List[str] = []
    branch_answers: List[str] = []

    prompt = (
        "You are solving a math problem using Tree-of-Thought reasoning.\n"
        "Generate one reasoning path and provide a final answer.\n\n"
        f"Problem: {question}\n\n"
        "Reasoning path:"
    )

    for _ in range(TOT_NUM_BRANCHES):
        raw, ans = _generate(prompt, model, tokenizer, max_new_tokens=TOT_MAX_NEW_TOKENS)
        branch_outputs.append(raw)
        branch_answers.append(ans)

    # Vote: pick the most common answer
    if not branch_answers:
        return "", ""

    from collections import Counter
    vote_counts = Counter(a for a in branch_answers if a)
    if vote_counts:
        best_answer = vote_counts.most_common(1)[0][0]
        best_idx = branch_answers.index(best_answer)
        return branch_outputs[best_idx], best_answer

    return branch_outputs[0], branch_answers[0]


def _generate(prompt: str, model, tokenizer, max_new_tokens: int) -> Tuple[str, str]:
    """Tokenize + generate + decode. Returns (raw_output, extracted_answer)."""
    try:
        import torch
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Strip the prompt tokens
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        raw = tokenizer.decode(generated, skip_special_tokens=True).strip()
        return raw, _extract_answer(raw)
    except Exception as exc:
        print(f"   ⚠️  Generation error: {exc}")
        return "", ""


def _extract_answer(text: str) -> str:
    """
    Extract the final numerical answer from generated text.
    Looks for patterns like 'the answer is X', '= X', or the last number.
    """
    import re
    text = text.strip()

    # Explicit answer markers
    for pattern in [
        r"(?:the\s+)?(?:final\s+)?answer\s*(?:is|=|:)\s*([+-]?\d[\d,\.]*)",
        r"\\boxed\{([^}]+)\}",
        r"=\s*([+-]?\d[\d,\.]*)\s*$",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", "").strip()

    # Fall back to last number in the text
    numbers = re.findall(r"[+-]?\d[\d,\.]*", text)
    if numbers:
        return numbers[-1].replace(",", "")
    return text[:50] if text else ""


def _is_correct(pred: str, gt: str) -> bool:
    """Numeric answer comparison with tolerance."""
    import re

    def _to_float(s: str) -> Optional[float]:
        s = s.strip().replace(",", "")
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    # Extract numbers if full strings given
    def _extract_num(s: str) -> Optional[float]:
        m = re.search(r"[+-]?\d[\d\.]*", str(s).replace(",", ""))
        return float(m.group()) if m else None

    p = _to_float(str(pred))
    g = _to_float(str(gt))

    if p is None:
        p = _extract_num(str(pred))
    if g is None:
        g = _extract_num(str(gt))

    if p is not None and g is not None:
        # Use 0.1% relative tolerance (or absolute 1e-3 for near-zero values)
        # so that rounding differences in model output don't count as wrong.
        return abs(p - g) < 1e-3 * max(1, abs(g))

    # String fallback
    return str(pred).strip().lower() == str(gt).strip().lower()


# ─────────────────────────── main evaluation loop ─────────────────────────────

def _compute_summary(checkpoint_mgr: CheckpointManager) -> Dict:
    """Build summary dict from checkpoint data."""
    df = checkpoint_mgr.checkpoint_to_dataframe()
    if df is None or (hasattr(df, "empty") and df.empty):
        return {}

    summary: Dict = {}
    for cat, grp in df.groupby("category"):
        summary[cat] = {
            "total":       len(grp),
            "cot_correct": int(grp["cot_correct"].sum()),
            "tot_correct": int(grp["tot_correct"].sum()),
        }
    return summary


def main() -> None:
    global _checkpoint_mgr, _start_time, _graph_path

    args = _parse_args()
    _start_time = time.time()

    # ── Register signal handler ──────────────────────────────────────────
    signal.signal(signal.SIGINT, handle_interrupt)

    # ── Checkpoint manager ───────────────────────────────────────────────
    _checkpoint_mgr = CheckpointManager(CHECKPOINT_FILE)

    if args.fresh or not RESUME_ENABLED:
        _checkpoint_mgr.clear()
        print("🆕 Starting fresh (checkpoint cleared).")
    else:
        resume_stats = _checkpoint_mgr.get_resume_stats()
        if resume_stats:
            total_done = sum(resume_stats.values())
            print(f"📂 Resuming from checkpoint: {total_done} samples already done")
            print(f"   Per category: {resume_stats}")
        else:
            print("🆕 No checkpoint found – starting from scratch.")

    # ── Load model ───────────────────────────────────────────────────────
    model, tokenizer = _load_model()

    # ── Discover datasets ────────────────────────────────────────────────
    dataset_files = _find_dataset_files()
    if not dataset_files:
        print("❌ No dataset files found. Check DATA_FOLDER in config.py.")
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    _graph_path = os.path.join(RESULTS_DIR, "evaluation_graphs.png")

    samples_done = _checkpoint_mgr.total_done()

    # ── Evaluation loop ───────────────────────────────────────────────────
    for stem, fpath in sorted(dataset_files.items()):
        category = DATASET_CATEGORY_MAP.get(stem, stem)

        try:
            df = _load_dataframe(fpath)
        except Exception as exc:
            print(f"⚠️  Could not load {fpath}: {exc}")
            continue

        q_col = _detect_question_col(df)
        a_col = _detect_answer_col(df)

        if q_col is None:
            print(f"⚠️  No question column found in {stem} – skipping.")
            continue

        # Cap samples per category
        df = df.head(MAX_SAMPLES_PER_CATEGORY).reset_index(drop=True)

        already_done = sum(
            1 for i in range(len(df)) if _checkpoint_mgr.is_done(category, i)
        )
        remaining = len(df) - already_done

        print(
            f"\n📂 {stem}  →  category: {category}  |  "
            f"total: {len(df)}  |  done: {already_done}  |  remaining: {remaining}"
        )

        if remaining == 0:
            print(f"   ✅ All samples already evaluated – skipping.")
            continue

        # Build iterator with optional tqdm progress bar
        iterator = df.iterrows()
        if _TQDM_AVAILABLE:
            iterator = tqdm(
                df.iterrows(),
                total=len(df),
                initial=already_done,
                desc=f"{category}",
                unit="sample",
            )

        for idx, row in iterator:
            # Skip already-done samples
            if _checkpoint_mgr.is_done(category, idx):
                continue

            question = str(row.get(q_col, "")).strip()
            gt = str(row.get(a_col, "")).strip() if a_col else ""

            if not question:
                continue

            # ── Evaluate ──────────────────────────────────────────────
            cot_raw, cot_pred = _run_cot(question, model, tokenizer)
            tot_raw, tot_pred = _run_tot(question, model, tokenizer)

            cot_ok = _is_correct(cot_pred, gt) if gt else False
            tot_ok = _is_correct(tot_pred, gt) if gt else False

            # ── Save checkpoint ───────────────────────────────────────
            _checkpoint_mgr.save_checkpoint(
                {
                    "category":    category,
                    "idx":         int(idx),
                    "question":    question[:200],
                    "cot_correct": int(cot_ok),
                    "tot_correct": int(tot_ok),
                    "cot_pred":    cot_pred,
                    "tot_pred":    tot_pred,
                    "gt":          gt,
                    "timestamp":   datetime.now().isoformat(),
                }
            )

            samples_done += 1

            # ── Auto-save partial reports every N samples ─────────────
            if AUTOSAVE_EVERY > 0 and (samples_done % AUTOSAVE_EVERY) == 0:
                elapsed = _elapsed_str()
                summary = _compute_summary(_checkpoint_mgr)
                generate_all_reports(
                    summary=summary,
                    df=_checkpoint_mgr.checkpoint_to_dataframe(),
                    runtime_str=elapsed,
                    graph_path=_graph_path if os.path.exists(_graph_path) else None,
                    partial=True,
                )
                print(f"  💾 Auto-saved at {samples_done} samples (elapsed: {elapsed})")

    # ── Final reports ─────────────────────────────────────────────────────
    print("\n\n🎉 Evaluation complete!")
    elapsed = _elapsed_str()
    print(f"   Total samples evaluated: {_checkpoint_mgr.total_done()}")
    print(f"   Elapsed time: {elapsed}")

    summary = _compute_summary(_checkpoint_mgr)
    generate_all_reports(
        summary=summary,
        df=_checkpoint_mgr.checkpoint_to_dataframe(),
        runtime_str=elapsed,
        graph_path=_graph_path if os.path.exists(_graph_path) else None,
        partial=False,
    )

    # ── Print quick summary table ─────────────────────────────────────────
    print("\n📊 Summary:")
    print(f"{'Category':<30} {'Questions':>9} {'CoT%':>7} {'ToT%':>7} {'Best':>6}")
    print("-" * 65)
    for cat, v in sorted(summary.items()):
        total = v["total"]
        cot_acc = round(100.0 * v["cot_correct"] / total, 1) if total else 0.0
        tot_acc = round(100.0 * v["tot_correct"] / total, 1) if total else 0.0
        best = "CoT" if cot_acc >= tot_acc else "ToT"
        print(f"{cat:<30} {total:>9} {cot_acc:>6.1f}% {tot_acc:>6.1f}% {best:>6}")


if __name__ == "__main__":
    main()
