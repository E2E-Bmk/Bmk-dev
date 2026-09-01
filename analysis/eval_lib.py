"""Shared helpers for Spec2Repo evaluation reporting.

Reads a results directory laid out as
``results/<agent>_<model>/<task_id>/result.json`` and normalises every task
into a :class:`Row`. Status classification mirrors the reporting convention:

  ok      -- score.status == "ok" (scored cleanly)
  partial -- status != "ok" but a denominator exists (atomic_total or
             integ_total > 0); the task ran but did not score cleanly
  zero    -- both totals are 0; nothing measurable

The average of a task is (atomic_passed + integ_passed) / (atomic_total +
integ_total); it is None when the denominator is 0.

The module is import-path independent: it locates the repo through
harness.core.layout, so it works from any checkout without hard-coded paths.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from harness.core import layout  # noqa: E402

RESULTS_ROOT = layout.ROOT / "results"
DATA_DIR = Path(__file__).resolve().parent / "_data"
ATTRIBUTION_FILE = DATA_DIR / "attribution.json"


@dataclass
class Row:
    task: str
    language: str
    status: str
    atomic_passed: int
    atomic_total: int
    integ_passed: int
    integ_total: int

    @property
    def total(self) -> int:
        return self.atomic_total + self.integ_total

    @property
    def passed(self) -> int:
        return self.atomic_passed + self.integ_passed

    @property
    def klass(self) -> str:
        if self.status == "ok":
            return "ok"
        return "partial" if self.total > 0 else "zero"

    @property
    def avg(self) -> Optional[float]:
        return (self.passed / self.total) if self.total else None


def result_dir(agent: str, model: str) -> Path:
    return RESULTS_ROOT / f"{agent}_{model}"


def iter_rows(run_dir: Path) -> Iterator[Row]:
    for p in sorted(run_dir.glob("*/result.json")):
        # Skip backup/replaced-result directories (e.g. "<id>.old"); only
        # count one live result per task.
        if p.parent.name.endswith(".old"):
            continue
        try:
            j = json.loads(p.read_text())
        except Exception:
            continue
        s = j.get("score") or {}
        yield Row(
            task=j.get("task_id", p.parent.name),
            language=j.get("language", "?"),
            status=str(s.get("status", "?")),
            atomic_passed=int(s.get("atomic_passed", 0) or 0),
            atomic_total=int(s.get("atomic_total", 0) or 0),
            integ_passed=int(s.get("integ_passed", 0) or 0),
            integ_total=int(s.get("integ_total", 0) or 0),
        )


def load_rows(agent: str, model: str) -> list[Row]:
    d = result_dir(agent, model)
    if not d.is_dir():
        raise SystemExit(f"no such run dir: {d}")
    rows = list(iter_rows(d))
    if not rows:
        raise SystemExit(f"no result.json under {d}")
    return rows


def load_attribution() -> dict:
    if not ATTRIBUTION_FILE.exists():
        return {}
    return json.loads(ATTRIBUTION_FILE.read_text())


def bucket_of(task: str, attribution: Optional[dict] = None) -> Optional[str]:
    """Return 'A'/'B'/'C' for a task per the curated attribution, else None."""
    attribution = attribution if attribution is not None else load_attribution()
    for key, letter in (("A_candidate_fail", "A"),
                         ("B_spec_gap", "B"),
                         ("C_pending", "C")):
        if task in attribution.get(key, []):
            return letter
    return None


def is_trusted(row: Row, attribution: Optional[dict] = None) -> bool:
    """A task's score is trusted when it scored cleanly (ok) or its failure is
    attributed to the candidate (bucket A)."""
    return row.klass == "ok" or bucket_of(row.task, attribution) == "A"


LANG_ORDER = {"python": 0, "java": 1, "rust": 2, "typescript": 3}


def lang_key(lang: str) -> int:
    return LANG_ORDER.get(lang, 9)
