"""
report_generator.py
────────────────────
Generates three output formats from evaluation results:

  1. CSV  → results/evaluation_report.csv   (summary)
            results/detailed_results.csv    (per-sample)
  2. HTML → results/evaluation_report.html  (self-contained, graphs embedded)
  3. PDF  → results/evaluation_report.pdf   (via fpdf2)

All functions accept either:
  - a pandas DataFrame (detailed, per-sample rows), or
  - a summary dict   {category: {"total": N, "cot_correct": M, "tot_correct": K}}
"""

from __future__ import annotations

import base64
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

from config import RESULTS_DIR, MODEL_NAME, SAVE_CSV, SAVE_HTML, SAVE_PDF


# ─────────────────────────────── helpers ──────────────────────────────────────

def _pct(num: int, denom: int) -> float:
    return round(100.0 * num / denom, 1) if denom else 0.0


def _build_summary_rows(summary: Dict) -> List[dict]:
    """
    summary format:
        { category: {"total": int, "cot_correct": int, "tot_correct": int} }
    Returns a list of row dicts suitable for CSV / HTML / PDF tables.
    """
    rows = []
    for cat, v in sorted(summary.items()):
        total = v.get("total", 0)
        cot_acc = _pct(v.get("cot_correct", 0), total)
        tot_acc = _pct(v.get("tot_correct", 0), total)
        diff = round(abs(cot_acc - tot_acc), 1)
        best = "CoT" if cot_acc >= tot_acc else "ToT"
        rows.append(
            {
                "Category":       cat,
                "Questions":      total,
                "CoT_Acc_Pct":    cot_acc,
                "ToT_Acc_Pct":    tot_acc,
                "Best_Method":    best,
                "Difference_Pct": diff,
            }
        )
    return rows


def _summary_from_df(df) -> Dict:
    """Build summary dict from a per-sample DataFrame."""
    summary: Dict = {}
    for cat, grp in df.groupby("category"):
        summary[cat] = {
            "total":       len(grp),
            "cot_correct": int(grp["cot_correct"].sum()),
            "tot_correct": int(grp["tot_correct"].sum()),
        }
    return summary


# ─────────────────────────── 1. CSV ───────────────────────────────────────────

def save_csv(summary: Dict, df=None, results_dir: str = RESULTS_DIR) -> None:
    """Save summary CSV and (optionally) detailed per-sample CSV."""
    os.makedirs(results_dir, exist_ok=True)
    rows = _build_summary_rows(summary)

    # Summary CSV
    summary_path = os.path.join(results_dir, "evaluation_report.csv")
    if _PANDAS_AVAILABLE:
        pd.DataFrame(rows).to_csv(summary_path, index=False)
    else:
        import csv
        if rows:
            with open(summary_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    print(f"✅ Summary CSV saved → {summary_path}")

    # Detailed CSV
    if df is not None and _PANDAS_AVAILABLE:
        detail_path = os.path.join(results_dir, "detailed_results.csv")
        df.to_csv(detail_path, index=False)
        print(f"✅ Detailed CSV saved → {detail_path}")


# ─────────────────────────── 2. HTML ──────────────────────────────────────────

def save_html(
    summary: Dict,
    runtime_str: str = "N/A",
    graph_path: Optional[str] = None,
    results_dir: str = RESULTS_DIR,
) -> None:
    """Generate a self-contained HTML report."""
    os.makedirs(results_dir, exist_ok=True)
    rows = _build_summary_rows(summary)

    total_questions = sum(r["Questions"] for r in rows)
    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Key findings
    if rows:
        best_cat  = max(rows, key=lambda r: max(r["CoT_Acc_Pct"], r["ToT_Acc_Pct"]))
        worst_cat = min(rows, key=lambda r: max(r["CoT_Acc_Pct"], r["ToT_Acc_Pct"]))
        cot_wins  = sum(1 for r in rows if r["Best_Method"] == "CoT")
        tot_wins  = len(rows) - cot_wins
        avg_cot   = round(sum(r["CoT_Acc_Pct"] for r in rows) / len(rows), 1)
        avg_tot   = round(sum(r["ToT_Acc_Pct"] for r in rows) / len(rows), 1)
        findings = [
            f"Best performing category: <strong>{best_cat['Category']}</strong> "
            f"(CoT {best_cat['CoT_Acc_Pct']}% / ToT {best_cat['ToT_Acc_Pct']}%)",
            f"Hardest category: <strong>{worst_cat['Category']}</strong> "
            f"(CoT {worst_cat['CoT_Acc_Pct']}% / ToT {worst_cat['ToT_Acc_Pct']}%)",
            f"CoT outperforms ToT in <strong>{cot_wins}</strong> of {len(rows)} categories",
            f"ToT outperforms CoT in <strong>{tot_wins}</strong> of {len(rows)} categories",
            f"Average accuracy — CoT: <strong>{avg_cot}%</strong>, ToT: <strong>{avg_tot}%</strong>",
        ]
    else:
        findings = ["No results available yet."]

    # Embed graph image as base64 (if file exists)
    graph_html = ""
    if graph_path and os.path.exists(graph_path):
        with open(graph_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        graph_html = (
            f'<h2 style="margin-top:40px;">📊 Performance Graphs</h2>'
            f'<img src="data:image/png;base64,{b64}" '
            f'style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15);" '
            f'alt="Evaluation Graphs"/>'
        )

    # Table rows HTML
    table_rows_html = ""
    for r in rows:
        best_color = "#d4edda" if r["Best_Method"] == "CoT" else "#fce8e6"
        table_rows_html += f"""
        <tr style="background:{best_color};">
          <td>{r['Category']}</td>
          <td style="text-align:center;">{r['Questions']}</td>
          <td style="text-align:center;color:#4A90D9;font-weight:bold;">{r['CoT_Acc_Pct']}%</td>
          <td style="text-align:center;color:#E8704A;font-weight:bold;">{r['ToT_Acc_Pct']}%</td>
          <td style="text-align:center;font-weight:bold;">{r['Best_Method']}</td>
          <td style="text-align:center;">{r['Difference_Pct']}%</td>
        </tr>"""

    findings_html = "".join(f"<li>{f}</li>" for f in findings)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>{MODEL_NAME} – Mathematical Reasoning Evaluation Report</title>
<style>
  body {{font-family:Arial,sans-serif;max-width:1100px;margin:0 auto;padding:20px;color:#333;}}
  h1 {{color:#1a237e;border-bottom:3px solid #1a237e;padding-bottom:10px;}}
  h2 {{color:#1a237e;margin-top:30px;}}
  .meta-table {{border-collapse:collapse;width:100%;margin-bottom:20px;}}
  .meta-table td {{padding:8px 14px;border:1px solid #ddd;}}
  .meta-table tr:nth-child(even) {{background:#f5f5f5;}}
  .result-table {{border-collapse:collapse;width:100%;}}
  .result-table th {{background:#1a237e;color:#fff;padding:10px 14px;text-align:left;}}
  .result-table td {{padding:9px 14px;border:1px solid #ddd;}}
  .result-table tr:hover {{filter:brightness(.96);}}
  .findings {{background:#f0f4ff;border-left:4px solid #1a237e;padding:14px 20px;border-radius:4px;}}
  .findings li {{margin:6px 0;line-height:1.6;}}
</style>
</head>
<body>
<h1>🧮 {MODEL_NAME} – Mathematical Reasoning Evaluation Report</h1>

<h2>📋 Metadata</h2>
<table class="meta-table">
  <tr><td><strong>Generated On</strong></td><td>{generated_on}</td></tr>
  <tr><td><strong>Total Questions</strong></td><td>{total_questions:,}</td></tr>
  <tr><td><strong>Total Runtime</strong></td><td>{runtime_str}</td></tr>
  <tr><td><strong>Model</strong></td><td>{MODEL_NAME}</td></tr>
</table>

<h2>📊 Performance by Category</h2>
<table class="result-table">
  <thead>
    <tr>
      <th>Category</th>
      <th>Questions</th>
      <th style="color:#9ecfff;">CoT Acc%</th>
      <th style="color:#ffc5b0;">ToT Acc%</th>
      <th>Best Method</th>
      <th>Difference</th>
    </tr>
  </thead>
  <tbody>{table_rows_html}
  </tbody>
</table>

<h2>🔍 Key Findings</h2>
<div class="findings"><ul>{findings_html}</ul></div>

{graph_html}

<p style="margin-top:40px;color:#888;font-size:.85em;">
  Generated by math_eval · {generated_on}
</p>
</body>
</html>"""

    out_path = os.path.join(results_dir, "evaluation_report.html")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"✅ HTML report saved → {out_path}")


# ─────────────────────────── 3. PDF ───────────────────────────────────────────

def save_pdf(
    summary: Dict,
    runtime_str: str = "N/A",
    graph_path: Optional[str] = None,
    results_dir: str = RESULTS_DIR,
) -> None:
    """Generate a PDF report using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("⚠️  fpdf2 not installed (pip install fpdf2). Skipping PDF report.")
        return

    os.makedirs(results_dir, exist_ok=True)
    rows = _build_summary_rows(summary)
    total_questions = sum(r["Questions"] for r in rows)
    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    COL_W = [42, 22, 22, 22, 28, 24]   # column widths (mm)
    HEADER_COLOR = (26, 35, 126)        # #1a237e
    ROW_COT_COLOR = (212, 237, 218)     # light green
    ROW_TOT_COLOR = (252, 232, 230)     # light red

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Title page header ──
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.rect(0, 0, 210, 40, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, "Mathematical Reasoning Evaluation Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(10, 24)
    pdf.cell(0, 8, MODEL_NAME, ln=True, align="C")
    pdf.set_text_color(0, 0, 0)

    # ── Metadata table ──
    pdf.set_xy(10, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Metadata", ln=True)
    pdf.set_font("Helvetica", "", 10)
    meta_rows = [
        ("Generated On", generated_on),
        ("Total Questions", f"{total_questions:,}"),
        ("Total Runtime", runtime_str),
        ("Model", MODEL_NAME),
    ]
    for label, value in meta_rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 7, label, border=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value, border=1, ln=True)

    pdf.ln(6)

    # ── Results table ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Performance by Category", ln=True)

    # Table header
    pdf.set_fill_color(*HEADER_COLOR)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Category", "Questions", "CoT Acc%", "ToT Acc%", "Best Method", "Diff%"]
    for w, h in zip(COL_W, headers):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    for r in rows:
        fill_color = ROW_COT_COLOR if r["Best_Method"] == "CoT" else ROW_TOT_COLOR
        pdf.set_fill_color(*fill_color)
        values = [
            r["Category"],
            str(r["Questions"]),
            f"{r['CoT_Acc_Pct']}%",
            f"{r['ToT_Acc_Pct']}%",
            r["Best_Method"],
            f"{r['Difference_Pct']}%",
        ]
        for w, v in zip(COL_W, values):
            pdf.cell(w, 7, v, border=1, fill=True, align="C")
        pdf.ln()

    pdf.ln(6)

    # ── Key findings ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Key Findings", ln=True)
    pdf.set_font("Helvetica", "", 10)

    if rows:
        best_cat  = max(rows, key=lambda r: max(r["CoT_Acc_Pct"], r["ToT_Acc_Pct"]))
        worst_cat = min(rows, key=lambda r: max(r["CoT_Acc_Pct"], r["ToT_Acc_Pct"]))
        cot_wins  = sum(1 for r in rows if r["Best_Method"] == "CoT")
        avg_cot   = round(sum(r["CoT_Acc_Pct"] for r in rows) / len(rows), 1)
        avg_tot   = round(sum(r["ToT_Acc_Pct"] for r in rows) / len(rows), 1)
        findings = [
            f"Best category: {best_cat['Category']} "
            f"(CoT {best_cat['CoT_Acc_Pct']}% / ToT {best_cat['ToT_Acc_Pct']}%)",
            f"Hardest category: {worst_cat['Category']} "
            f"(CoT {worst_cat['CoT_Acc_Pct']}% / ToT {worst_cat['ToT_Acc_Pct']}%)",
            f"CoT outperforms ToT in {cot_wins} of {len(rows)} categories",
            f"Average accuracy - CoT: {avg_cot}%, ToT: {avg_tot}%",
        ]
    else:
        findings = ["No results available yet."]

    for finding in findings:
        pdf.cell(5, 6, chr(149))   # bullet (•)
        pdf.cell(0, 6, finding, ln=True)

    # ── Graph image ──
    if graph_path and os.path.exists(graph_path):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Evaluation Graphs", ln=True)
        pdf.image(graph_path, x=10, w=190)

    out_path = os.path.join(results_dir, "evaluation_report.pdf")
    pdf.output(out_path)
    print(f"✅ PDF report saved → {out_path}")


# ─────────────────────────── unified entry point ──────────────────────────────

def generate_all_reports(
    summary: Optional[Dict] = None,
    df=None,
    runtime_str: str = "N/A",
    graph_path: Optional[str] = None,
    results_dir: str = RESULTS_DIR,
    partial: bool = False,
) -> None:
    """
    Generate all enabled report formats.

    Parameters
    ----------
    summary    : pre-computed summary dict (if None, built from *df*)
    df         : per-sample DataFrame (used when summary is None and for detailed CSV)
    runtime_str: human-readable elapsed time string
    graph_path : path to evaluation_graphs.png
    results_dir: output directory
    partial    : if True, adds "(partial)" label to runtime_str
    """
    if summary is None:
        if df is None or not _PANDAS_AVAILABLE:
            print("⚠️  No data to generate reports from.")
            return
        summary = _summary_from_df(df)

    if partial:
        runtime_str = f"{runtime_str} (partial)"

    if SAVE_CSV:
        save_csv(summary, df=df, results_dir=results_dir)
    if SAVE_HTML:
        save_html(summary, runtime_str=runtime_str, graph_path=graph_path, results_dir=results_dir)
    if SAVE_PDF:
        save_pdf(summary, runtime_str=runtime_str, graph_path=graph_path, results_dir=results_dir)
