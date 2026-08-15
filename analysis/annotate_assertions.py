#!/usr/bin/env python3
"""
Assertion-kind annotator for the Spec2Repo oracle.

Classifies every oracle test function by what its assertions actually verify:

  positive      at least one assertion checks a concrete produced value or
                observable side effect (equality, membership, content, ==0 exit)
                OR the test checks two mutually exclusive directions (see below)
  failure_path  all checks verify rejection: pytest.raises, `is False`,
                `is None`, `not x`, non-zero exit codes, exception-shaped helpers
  shape         all checks are type/attribute existence (isinstance, hasattr,
                callable) without any value verification
  no_check      no assertion-like construct found

The operative question is: does a trivial constant strategy exist that passes
every check in the test? Signals are therefore grouped by which trivial
strategy satisfies them:

  exc_raise     pytest.raises / pytest.fail guards — satisfied by a stub that
                raises on every call
  falsy_return  `is None` / `is False` / `not x` — satisfied by a stub that
                returns None/falsy on every call (requires a NORMAL return)
  proc_fail     non-zero exit codes / returncode != 0 — satisfied by a stub
                whose process always crashes (same strategy as exc_raise)

A test containing BOTH exc_raise and falsy_return signals verifies a
bidirectional contract (e.g. vcr matchers: match -> returns None, mismatch ->
raises AssertionError). No constant strategy passes both, so it is classified
positive. exc_raise + proc_fail remain failure_path (one crash-everything
strategy satisfies both).

Helper indirection (e.g. a local `assert_raises` or `_assert_usage_failure`)
is resolved by classifying module helpers first and propagating their signals
into callers.

Output:
  analysis/annotations/assertion_kinds.json   {task: {fn_key: record}}
  analysis/annotations/review_queue.md        low-confidence rows for human review

Usage:
  python analysis/annotate_assertions.py [--root <repo>] [--task <id> ...]
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SHAPE_CALLS = {"isinstance", "issubclass", "hasattr", "callable"}
FAIL_HELPER_NAME_HINTS = ("raise", "fail", "error", "reject", "nonzero", "invalid")


def _call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _returncode_like(node: ast.AST) -> bool:
    src = ast.dump(node)
    return any(k in src for k in ("returncode", "exit_code", "retcode", "exitcode",
                                  "'code'", "status"))


def classify_assert(test: ast.expr) -> str:
    """Classify one `assert <test>` into a granular signal.

    Signals: positive | exc_raise | falsy_return | proc_fail | shape
    """
    # Comparisons
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op, right = test.ops[0], test.comparators[0]
        left = test.left
        if isinstance(right, ast.Constant):
            v = right.value
            if v is False and isinstance(op, (ast.Is, ast.Eq)):
                return "falsy_return"
            if v is None and isinstance(op, ast.Is):
                return "falsy_return"
            if v is None and isinstance(op, ast.IsNot):
                return "positive"
            if v is True and isinstance(op, (ast.Is, ast.Eq)):
                return "positive"
            if v == 0 and isinstance(op, (ast.NotEq, ast.Gt, ast.GtE)) and _returncode_like(left):
                return "proc_fail"
            if v == 0 and isinstance(op, ast.Eq) and _returncode_like(left):
                return "positive"
            if isinstance(v, int) and v != 0 and isinstance(op, ast.Eq) and _returncode_like(left):
                return "proc_fail"
        # len(x) == 0 / x == [] / x == {} — emptiness checks lean failure-ish but
        # are legitimate value contracts (e.g. "expired items removed"): positive.
        return "positive"
    # Boolean negation: assert not x
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return "falsy_return"
    # Call-shaped: isinstance/hasattr/callable -> shape
    if isinstance(test, ast.Call):
        if _call_name(test) in SHAPE_CALLS:
            return "shape"
        return "positive"
    # assert x.attr / assert x  (truthiness)
    return "positive"


class FunctionClassifier(ast.NodeVisitor):
    """Collect granular assertion signals within one function body."""

    def __init__(self, helper_signals: dict[str, set]):
        self.signals: list[str] = []
        self.used_helpers: list[str] = []
        self.helper_signals = helper_signals

    def visit_Assert(self, node: ast.Assert):
        self.signals.append(classify_assert(node.test))
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        for item in node.items:
            c = item.context_expr
            if isinstance(c, ast.Call) and _call_name(c) == "raises":
                self.signals.append("exc_raise")
            elif isinstance(c, ast.Call) and _call_name(c) == "warns":
                self.signals.append("positive")
        self.generic_visit(node)

    visit_AsyncWith = visit_With

    def visit_Call(self, node: ast.Call):
        name = _call_name(node)
        if name in self.helper_signals:
            self.signals.extend(self.helper_signals[name])
            self.used_helpers.append(name)
        elif name == "fail":  # pytest.fail guarding a branch
            self.signals.append("exc_raise")
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise):
        # `raise AssertionError(...)` used as manual check
        exc = node.exc
        target = ""
        if isinstance(exc, ast.Call):
            target = getattr(exc.func, "id", getattr(exc.func, "attr", ""))
        elif isinstance(exc, ast.Name):
            target = exc.id
        if target == "AssertionError":
            self.signals.append("manual_check")
        self.generic_visit(node)


def aggregate(signals: list[str]) -> str:
    """Reduce granular signals to the test's kind.

    A test is positive if any single check verifies a produced value, or if
    its checks rule out every trivial constant strategy: `exc_raise` is
    satisfied by an always-raising stub, `falsy_return` by an always-None
    stub — a test requiring BOTH cannot be satisfied by either stub alone.
    `proc_fail` and `exc_raise` fall to the same crash-everything strategy,
    so their combination stays failure_path.
    """
    real = [s for s in signals if s != "manual_check"]
    if not real and "manual_check" in signals:
        return "failure_path"  # manual raise AssertionError guards, no value asserts
    if not real:
        return "no_check"
    kinds = set(real)
    if "positive" in kinds:
        return "positive"
    if "exc_raise" in kinds and "falsy_return" in kinds:
        return "positive"  # bidirectional contract, no constant stub passes
    if kinds <= {"shape"}:
        return "shape"
    return "failure_path"


def classify_helpers(tree: ast.Module) -> dict[str, set]:
    """Compute the signal set each module-level helper contributes to callers.

    Two passes so helpers that call other helpers resolve one level deep.
    A helper with no signals but a swallowing try/except and a failure-hinting
    name (e.g. `_expect_error`) contributes `exc_raise`.
    """
    helper_nodes = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("test")
    ]
    signals: dict[str, set] = {}
    for _ in range(2):
        for n in helper_nodes:
            fc = FunctionClassifier(signals)
            fc.visit(n)
            sig = {s for s in fc.signals if s != "manual_check"}
            if "manual_check" in fc.signals:
                sig.add("exc_raise")
            if not sig:
                has_except = any(isinstance(s, ast.Try) for s in ast.walk(n))
                if has_except and any(h in n.name.lower() for h in FAIL_HELPER_NAME_HINTS):
                    sig = {"exc_raise"}
            signals[n.name] = sig
    return {k: v for k, v in signals.items() if v}


def annotate_file(path: Path) -> dict[str, dict]:
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    tree = ast.parse(src, filename=str(path))
    helper_signals = classify_helpers(tree)
    stem = path.stem
    out: dict[str, dict] = {}

    def walk(body, prefix=""):
        for node in body:
            if isinstance(node, ast.ClassDef):
                walk(node.body, prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                fc = FunctionClassifier(helper_signals)
                fc.visit(node)
                kind = aggregate(fc.signals)
                counts = Counter(s for s in fc.signals if s != "manual_check")
                low_confidence = (
                    kind == "no_check"
                    or (kind == "positive" and "positive" not in counts)  # bidirectional rule fired
                    or (bool(fc.used_helpers) and kind != "positive")
                )
                out[f"{stem}::{prefix}{node.name}"] = {
                    "kind": kind,
                    "signals": dict(counts),
                    "helpers": sorted(set(fc.used_helpers)),
                    "low_confidence": bool(low_confidence),
                }
    walk(tree.body)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--task", action="append", default=None)
    args = ap.parse_args()

    root = Path(args.root)
    oracle_root = root / "oracle"
    out_dir = root / "analysis" / "annotations"
    out_dir.mkdir(parents=True, exist_ok=True)

    task_ids = args.task or sorted(d.name for d in oracle_root.iterdir() if d.is_dir())
    all_annotations: dict[str, dict] = {}
    review_rows: list[str] = []

    print(f"{'task':44s} {'fns':>4s} {'pos':>4s} {'fail':>5s} {'shape':>5s} {'none':>4s} {'review':>6s}")
    for tid in task_ids:
        tdir = oracle_root / tid
        ann: dict[str, dict] = {}
        for fname in ("test_atomic.py", "test_integration.py"):
            p = tdir / fname
            if p.exists():
                ann.update(annotate_file(p))
        all_annotations[tid] = ann
        c = Counter(v["kind"] for v in ann.values())
        review = [k for k, v in ann.items() if v["low_confidence"]]
        for k in review:
            review_rows.append(f"| {tid} | {k} | {ann[k]['kind']} | {ann[k]['signals']} | {','.join(ann[k]['helpers'])} |")
        print(f"{tid:44s} {len(ann):>4d} {c['positive']:>4d} {c['failure_path']:>5d} "
              f"{c['shape']:>5d} {c['no_check']:>4d} {len(review):>6d}")

    out_path = out_dir / "assertion_kinds.json"
    out_path.write_text(json.dumps(all_annotations, indent=1, sort_keys=True), encoding="utf-8")

    total = Counter(v["kind"] for ann in all_annotations.values() for v in ann.values())
    n = sum(total.values())
    print(f"\nTOTAL {n} tests: positive={total['positive']} ({100*total['positive']/n:.1f}%) "
          f"failure_path={total['failure_path']} ({100*total['failure_path']/n:.1f}%) "
          f"shape={total['shape']} no_check={total['no_check']}")

    review_path = out_dir / "review_queue.md"
    header = (
        "# Assertion-kind review queue\n\n"
        "Rows the classifier is least confident about. Review the test source and,\n"
        "if the kind is wrong, add an override entry to `assertion_overrides.json`\n"
        "as {\"<task>\": {\"<fn_key>\": \"positive|failure_path|shape\"}}.\n\n"
        "| task | test | kind | signals | helpers |\n|---|---|---|---|---|\n"
    )
    review_path.write_text(header + "\n".join(review_rows) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path}")
    print(f"wrote {review_path} ({len(review_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
