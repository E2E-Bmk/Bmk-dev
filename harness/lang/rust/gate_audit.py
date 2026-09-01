#!/usr/bin/env python3
"""gate_audit.py — one gate table across every Rust task.

Gate evidence lives in two places depending on which harness a task used:
`eval/runs/<gate>/<id>/result.json` (eval/run_score.sh) or
`oracle/gates/run_<gate>.log` (oracle/gates/run_gates.sh). Reading only one
reports a false gap, so both are checked and the source is named.
"""
import json
import os
import re
import subprocess
import sys

BMK = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
# This is a per-language tool, so it reads the Rust bucket rather than all of wip/.
WIP = os.path.join(BMK, "wip", "rust")

SECTIONS = {
    "overview": ["product overview"],
    "scope": ["scope", "non-goals"],
    "surface": ["installable surface", "public import surface",
                "public interface", "public api"],
    "state": ["product state model", "state model"],
    "errors": ["error semantics", "validation and error reporting"],
    "cross_view": ["cross-view invariants", "cross-component invariants"],
    "workflow": ["representative workflow"],
    "non_goals": ["non-goals"],
    "invocation": ["invocation protocol", "public interface", "public api"],
    "environment": ["environment"],
    "evaluation": ["evaluation notes", "implementation guidance",
                   "assessment notes"],
}
FORBIDDEN = ["task_id", "source_boundary", "candidate-visible", "benchmark",
             "oracle", "judge", "scoring"]


def gate_from_result(path):
    if not os.path.isfile(path):
        return None
    s = json.load(open(path))["score"]
    if s.get("status") != "ok":
        return {"src": "result.json", "status": s.get("status"),
                "ap": None, "at": None, "ip": None, "it": None}
    return {"src": "result.json", "status": "ok",
            "ap": s["atomic_passed"], "at": s["atomic_total"],
            "ip": s["integ_passed"], "it": s["integ_total"]}


def gate_from_log(path):
    """Read the libtest-json tallies the gate printed. `passed` always counts
    'ok' events, so the reference and dummy readings are the same measurement
    and only the expected value differs."""
    if not os.path.isfile(path):
        return None
    tallies = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("tally:"):
            try:
                tallies.append(json.loads(line[len("tally:"):].strip().replace("'", '"')))
            except Exception:
                return None
    if len(tallies) != 2:
        return None
    a, i = tallies
    return {"src": "gates.log", "status": "ok",
            "ap": a.get("ok", 0), "at": sum(a.values()),
            "ip": i.get("ok", 0), "it": sum(i.values())}


def gate(wip, tid, name):
    r = gate_from_result(f"{wip}/eval/runs/{name}/{tid}/result.json")
    if r and r["status"] == "ok":
        return r
    g = gate_from_log(f"{wip}/oracle/gates/run_{name}.log")
    return g or r


def spec_sections(spec_path):
    if not os.path.isfile(spec_path):
        return None, None
    text = open(spec_path, encoding="utf-8", errors="replace").read()
    # The wip spec carries an internal HTML header that legitimately names
    # task_id and source_boundary; graduation strips it. Scanning it unstripped
    # reports a leak on every task.
    text = re.sub(r"^<!--.*?-->\s*\n?", "", text, count=1, flags=re.DOTALL)
    heads = [h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)]
    missing = [k for k, pats in SECTIONS.items()
               if not any(p in h for h in heads for p in pats)]
    stripped = re.sub(r"`[^`]*`", " ", text).lower()
    leaks = [t for t in FORBIDDEN if re.search(rf"\b{re.escape(t)}\b", stripped)]
    return missing, leaks


def lint_state(wip):
    p = f"{wip}/filter/lint_result.txt"
    if not os.path.isfile(p):
        return "ABSENT", False
    first = open(p, encoding="utf-8", errors="replace").readline().strip()
    verdict = first.split()[0] if first else "EMPTY"
    lint_mt = os.path.getmtime(p)
    newest = lint_mt
    for root, _, files in os.walk(f"{wip}/oracle"):
        if "/gates" in root or "/target" in root:
            continue
        for f in files:
            newest = max(newest, os.path.getmtime(os.path.join(root, f)))
    return verdict, lint_mt >= newest


def best_score(wip, tid):
    """Highest-confidence agent measurement: sigfix probe beats a raw error run."""
    for run in ("sigfix", "_probe_sigfix", "probe-qwen3.8-max", "qwen3.8-max"):
        p = f"{wip}/eval/runs/{run}/{tid}/result.json"
        if not os.path.isfile(p):
            continue
        s = json.load(open(p))["score"]
        if s.get("status") != "ok":
            continue
        t = s["atomic_passed"] + s["integ_passed"]
        n = s["atomic_total"] + s["integ_total"]
        return run, t, n, 100.0 * t / n if n else 0.0
    return None, None, None, None


def counts(wip):
    def n(sub):
        try:
            out = subprocess.run(["grep", "-rc", r"#\[test\]", f"{wip}/oracle/{sub}"],
                                 capture_output=True, text=True).stdout
            return sum(int(l.rsplit(":", 1)[1]) for l in out.strip().split("\n") if ":" in l)
        except Exception:
            return 0
    return n("atomic"), n("integration")


def main():
    ids = sys.argv[1:] or sorted(
        d for d in os.listdir(WIP)
        if os.path.isdir(f"{WIP}/{d}/oracle") and not d.startswith("_"))
    rows = []
    for tid in ids:
        wip = f"{WIP}/{tid}"
        ref, dum = gate(wip, tid, "reference"), gate(wip, tid, "dummy")
        missing, leaks = spec_sections(f"{wip}/spec/spec_v1.md")
        verdict, fresh = lint_state(wip)
        run, t, n, pct = best_score(wip, tid)
        a, i = counts(wip)
        rows.append(dict(id=tid, ref=ref, dum=dum, missing=missing, leaks=leaks,
                         lint=verdict, fresh=fresh, run=run, t=t, n=n, pct=pct,
                         a=a, i=i))

    def g(x, want_zero=False):
        if not x:
            return "MISSING"
        if x["status"] != "ok":
            return x["status"]
        p, tot = x["ap"] + x["ip"], x["at"] + x["it"]
        good = (p == 0) if want_zero else (p == tot and tot > 0)
        return f"{'OK ' if good else 'BAD'} {p}/{tot}[{x['src'][:5]}]"

    print(f"{'task':34} {'ref':18} {'dummy':18} {'lint':10} {'a/i':9} {'score':22} sections")
    for r in rows:
        sc = f"{r['run']} {r['t']}/{r['n']}={r['pct']:.1f}%" if r["run"] else "-"
        if r["missing"] is None:
            sec = "NO SPEC"
        else:
            sec = "ok" if r["missing"] == [] else f"miss:{len(r['missing'])}"
            if r["leaks"]:
                sec += f" LEAK:{','.join(r['leaks'])}"
        lint = r["lint"] + ("" if r["fresh"] else "!stale")
        print(f"{r['id']:34} {g(r['ref']):18} {g(r['dum'], True):18} "
              f"{lint:10} {r['a']}/{r['i']:<5} {sc:22} {sec}")


if __name__ == "__main__":
    main()
