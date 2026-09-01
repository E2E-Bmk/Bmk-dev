"""Attribution report for non-clean tasks in an evaluation run.

For every task that did not score cleanly (status != ok) this walks the curated
attribution buckets and, as reproducible supporting evidence, runs the oracle
import lint over each task's atomic oracle:

  PASS           lint found no spec/oracle symbol mismatch
  FAIL(n)        lint found n symbols read by the oracle but absent from spec
  oracle-missing lint could not locate a test_atomic.py / java atomic dir
                 (expected for rust Cargo-layout oracles: the lint does not
                 cover them)

Views (``--view``):
  report  per-task table grouped by bucket A/B/C (with lint verdict)
  verify  check the curated buckets exactly cover the zero-score partial tasks

Usage:
  python -m analysis.attribution --model qwen3.8-max --view report
  python -m analysis.attribution --model qwen3.8-max --view verify
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from analysis import eval_lib as E
from harness.core import layout


def lint_verdict(task: str) -> str:
    try:
        spec = layout.spec_path(task)
    except Exception:
        return "no-spec"
    if not spec.exists():
        return "no-spec"
    try:
        out = subprocess.run(
            [sys.executable, "-m", "harness.core.oracle_import_lint", task, str(spec)],
            cwd=str(E.layout.ROOT), capture_output=True, text=True, timeout=120,
        ).stdout
    except Exception as exc:  # pragma: no cover
        return f"error:{exc}"
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        return "no-output"
    if lines[0].startswith("LINT_PASS"):
        return "PASS"
    if any("missing" in l for l in lines):
        return "oracle-missing"
    return f"FAIL({len(lines) - 1})"


def _non_ok(rows):
    return [r for r in rows if r.klass != "ok"]


def view_report(rows, attr):
    non_ok = _non_ok(rows)
    order = {"A": 0, "B": 1, "C": 2, None: 3}
    non_ok.sort(key=lambda r: (order[E.bucket_of(r.task, attr)],
                               E.lang_key(r.language), r.task))
    cur = object()
    for r in non_ok:
        b = E.bucket_of(r.task, attr)
        if b != cur:
            cur = b
            title = {"A": "A 候选真实失败(可信)", "B": "B 出题缺口",
                     "C": "C 待细核"}.get(b, "未归属 (other partial / zero)")
            print(f"\n--- {title} ---")
        print(f"  {r.language:11} {r.task:52} {r.klass:8} lint={lint_verdict(r.task)}")
    print()


def view_verify(rows, attr):
    # zero-score partial = klass partial with 0 passed; these are what the
    # A/B/C curation is meant to cover exactly.
    zero_part = {r.task for r in rows if r.klass == "partial" and r.passed == 0}
    curated = set(attr.get("A_candidate_fail", [])) | set(
        attr.get("B_spec_gap", [])) | set(attr.get("C_pending", []))
    missing = sorted(zero_part - curated)
    extra = sorted(curated - zero_part)
    print(f"zero-score partial: {len(zero_part)}")
    print(f"curated A+B+C     : {len(curated)}")
    print(f"missing (partial not curated): {missing}")
    print(f"extra   (curated not partial): {extra}")
    print("OK" if not missing and not extra else "MISMATCH")


VIEWS = {"report": view_report, "verify": view_verify}


def main():
    ap = argparse.ArgumentParser(description="Attribution report")
    ap.add_argument("--agent", default="minisweagent")
    ap.add_argument("--model", required=True)
    ap.add_argument("--view", choices=list(VIEWS), default="report")
    args = ap.parse_args()
    rows = E.load_rows(args.agent, args.model)
    attr = E.load_attribution()
    VIEWS[args.view](rows, attr)


if __name__ == "__main__":
    main()
