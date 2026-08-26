"""Emit evaluation ledgers from a results directory.

Views (``--view``):
  ledger  full per-task ledger with status class and pass/total counts
  trust   trust / untrust split summary plus rate roll-ups
  avg     seven-column per-task table (语言, 题, 均分, a分, i分, 测试总数, 备注)

"Trusted" tasks are those scored cleanly (status ok) plus the tasks whose
zero-score failure is attributed to the candidate (bucket A in
analysis/_data/attribution.json). Everything else is untrusted: authoring gaps
(bucket B), pending review (bucket C), any other partial, and zero-denominator
tasks.

Usage:
  python -m analysis.ledger --model qwen3.8-max --view avg
  python -m analysis.ledger --agent minisweagent --model qwen3.8-max --view trust
"""
from __future__ import annotations

import argparse

from analysis import eval_lib as E


def _rate(passed: int, total: int) -> str:
    return f"{passed}/{total}={100*passed/total:.1f}%" if total else f"{passed}/{total}=  -  "


def _pct(passed: int, total: int) -> str:
    return f"{100*passed/total:.1f}%" if total else "  -  "


def _roll(rows):
    ap = sum(r.atomic_passed for r in rows)
    at = sum(r.atomic_total for r in rows)
    ip = sum(r.integ_passed for r in rows)
    it = sum(r.integ_total for r in rows)
    tot = at + it
    avg = (ap + ip) / tot if tot else None
    return ap, at, ip, it, avg


def _sorted(rows):
    # language groups, then atomic rate desc, then task name
    def akey(r):
        arate = (r.atomic_passed / r.atomic_total) if r.atomic_total else -1.0
        return (E.lang_key(r.language), -arate, r.task)
    return sorted(rows, key=akey)


def view_ledger(rows, attr):
    for r in _sorted(rows):
        b = E.bucket_of(r.task, attr) or ""
        print(f"{r.language:11} {r.task:52} {r.klass:8} {b:2} "
              f"a {_rate(r.atomic_passed, r.atomic_total):14} "
              f"i {_rate(r.integ_passed, r.integ_total):14}")
    print(f"\ntotal tasks: {len(rows)}")
    from collections import Counter
    c = Counter(r.klass for r in rows)
    print("class:", dict(c))


def view_trust(rows, attr):
    trusted = [r for r in rows if E.is_trusted(r, attr)]
    untrusted = [r for r in rows if not E.is_trusted(r, attr)]
    ok = [r for r in rows if r.klass == "ok"]
    a = [r for r in trusted if r.klass != "ok"]

    def line(name, rows_):
        ap, at, ip, it, avg = _roll(rows_)
        av = f"{100*avg:.1f}%" if avg is not None else "  -  "
        print(f"{name:22} n={len(rows_):3}  均分 {av:6}  "
              f"atomic {_rate(ap, at):14}  integ {_rate(ip, it):14}")

    print("=== 可信榜单 (OK + A) ===")
    line("trusted total", trusted)
    line("  OK", ok)
    line("  A candidate-fail", a)
    print("\n=== 不可信榜单 ===")
    line("untrusted total", untrusted)
    for letter, key in (("B spec-gap", "B_spec_gap"),
                        ("C pending", "C_pending")):
        sub = [r for r in untrusted if r.task in attr.get(key, [])]
        line("  " + letter, sub)
    partial_other = [r for r in untrusted
                     if r.klass == "partial" and not E.bucket_of(r.task, attr)]
    zero = [r for r in untrusted if r.klass == "zero"]
    line("  other partial", partial_other)
    line("  zero-denominator", zero)
    print(f"\n合计 trusted {len(trusted)} + untrusted {len(untrusted)} = {len(rows)}")


def view_avg(rows, attr):
    # seven columns: 语言, 题, 均分, a分, i分, 测试总数, 备注
    hdr = ("语言", "题", "均分", "a分", "i分", "测试总数", "备注")
    print("{:11} {:52} {:7} {:14} {:14} {:8} {}".format(*hdr))
    for r in _sorted(rows):
        b = E.bucket_of(r.task, attr)
        note = {"A": "候选失败(可信)", "B": "出题缺口", "C": "待细核"}.get(b, "")
        if not note:
            note = "OK" if r.klass == "ok" else ("zero" if r.klass == "zero" else "partial")
        avg = f"{100*r.avg:.1f}%" if r.avg is not None else "  -  "
        print("{:11} {:52} {:>7} {:14} {:14} {:>8} {}".format(
            r.language, r.task, avg,
            f"{r.atomic_passed}/{r.atomic_total}",
            f"{r.integ_passed}/{r.integ_total}",
            r.total, note))
    ap, at, ip, it, avg = _roll(rows)
    av = f"{100*avg:.1f}%" if avg is not None else "-"
    print(f"\n全部 {len(rows)} 题  汇总均分 {av}  "
          f"atomic {_rate(ap, at)}  integ {_rate(ip, it)}")


VIEWS = {"ledger": view_ledger, "trust": view_trust, "avg": view_avg}


def main():
    ap = argparse.ArgumentParser(description="Spec2Repo evaluation ledger")
    ap.add_argument("--agent", default="minisweagent")
    ap.add_argument("--model", required=True)
    ap.add_argument("--view", choices=list(VIEWS), default="trust")
    args = ap.parse_args()
    rows = E.load_rows(args.agent, args.model)
    attr = E.load_attribution()
    VIEWS[args.view](rows, attr)


if __name__ == "__main__":
    main()
