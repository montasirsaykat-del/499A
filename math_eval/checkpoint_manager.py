"""
checkpoint_manager.py
─────────────────────
Atomic checkpoint save/load so that evaluation can be resumed after
an interruption (Ctrl-C, power-cut, session timeout, …).

Checkpoint file format
──────────────────────
A single JSON file whose top-level value is a list of entry dicts:

[
  {
    "category":    "Arithmetic",
    "idx":         0,
    "question":    "...",
    "cot_correct": 1,
    "tot_correct": 0,
    "cot_pred":    "42",
    "tot_pred":    "40",
    "gt":          "42",
    "timestamp":   "2026-03-05T10:00:00.000000"
  },
  ...
]

Atomicity
─────────
Writes are done via a temp-file + rename pattern so that a Ctrl-C
mid-write never corrupts the checkpoint file.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

from config import CHECKPOINT_FILE, RESULTS_DIR


class CheckpointManager:
    """Manages incremental saving and loading of evaluation progress."""

    def __init__(self, checkpoint_file: str = CHECKPOINT_FILE):
        self.checkpoint_file = checkpoint_file
        self._entries: List[dict] = []
        self._done: Set[Tuple[str, int]] = set()

        os.makedirs(RESULTS_DIR, exist_ok=True)
        self._load()

    # ─────────────────────────────── public API ───────────────────────────────

    def is_done(self, category: str, idx: int) -> bool:
        """Return True if (category, idx) has already been evaluated."""
        return (category, idx) in self._done

    def save_checkpoint(self, entry: dict) -> None:
        """
        Append *entry* to the checkpoint file using an atomic write.

        Required keys in *entry*:
            category, idx, question, cot_correct, tot_correct,
            cot_pred, tot_pred, gt, timestamp
        """
        # Add timestamp if missing
        entry.setdefault("timestamp", datetime.now().isoformat())

        self._entries.append(entry)
        self._done.add((entry["category"], entry["idx"]))
        self._atomic_write()

    def load_checkpoint(self) -> List[dict]:
        """Return the full list of already-saved entries."""
        return list(self._entries)

    def get_resume_stats(self) -> Dict[str, int]:
        """
        Return a dict mapping category → number of completed samples.
        Empty dict means no prior checkpoint exists.
        """
        stats: Dict[str, int] = {}
        for e in self._entries:
            stats[e["category"]] = stats.get(e["category"], 0) + 1
        return stats

    def checkpoint_to_dataframe(self):
        """Convert checkpoint entries to a pandas DataFrame.

        Returns None (not raises) when pandas is not installed.
        """
        if not _PANDAS_AVAILABLE:
            print("⚠️  pandas not installed – cannot build DataFrame.")
            return None
        if not self._entries:
            return pd.DataFrame()
        return pd.DataFrame(self._entries)

    def total_done(self) -> int:
        """Total number of samples already evaluated."""
        return len(self._entries)

    def clear(self) -> None:
        """Delete the checkpoint file and reset in-memory state."""
        self._entries = []
        self._done = set()
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print(f"🗑️  Checkpoint cleared: {self.checkpoint_file}")

    # ─────────────────────────────── internals ────────────────────────────────

    def _load(self) -> None:
        """Load existing checkpoint from disk (if present)."""
        if not os.path.exists(self.checkpoint_file):
            return
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                self._entries = data
                self._done = {(e["category"], e["idx"]) for e in data}
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"⚠️  Checkpoint file corrupt ({exc}); starting fresh.")
            self._entries = []
            self._done = set()

    def _atomic_write(self) -> None:
        """Write entries to a temp file then rename — safe against Ctrl-C."""
        dir_name = os.path.dirname(self.checkpoint_file) or "."
        # Use same directory so rename is on the same filesystem
        fd, tmp_path = tempfile.mkstemp(
            dir=dir_name, prefix=".checkpoint_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._entries, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.checkpoint_file)  # atomic on POSIX & Win
        except Exception:
            # Clean up tmp file on error; do NOT swallow the exception
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
