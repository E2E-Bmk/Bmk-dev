#!/usr/bin/env python3
"""Measure how much of a spec's prose is actually pinned by clause quotes.

verify_clauses.py answers "does every clause quote still exist in the spec?".
That is a check for *dangling quotes*. It says nothing about the opposite and
more dangerous failure: spec prose that no clause quotes at all, which is
unpinned behaviour an implementer can contradict with nothing going red.

This tool measures absence directly. It normalises the spec the same way
verify_clauses.py does, marks every character covered by some clause quote, and
reports the uncovered runs. There is no marker vocabulary to be short of, which
is the failure mode of presence-detectors: a scan that looks for known phrases
can only find the gaps someone already thought of.

GATES (both learned from false-positive incidents; do not remove)

  1. Verbatim fraction is computed FIRST and the run REFUSES below --min-verbatim
     (default 0.95). A substring instrument pointed at a stale or paraphrasing
     clause set reports near-maximum findings, and a high finding count reads as
     severity when it actually means "wrong tool, moving target". One task was
     flagged 9-of-13 purely for being mid-rewrite.

  2. mtime skew is reported, and clauses older than the spec is called out. It
     is the cheap tell for a clause set that has not caught up with a spec edit.

Believe a green only if you have seen this tool go red on a seeded gap:
    --selftest   runs that negative control and exits.

Usage:
    clause_span_coverage.py SPEC CLAUSES [--section REGEX] [--min-run N]
                            [--min-verbatim F] [--oracle DIR] [--quiet]
    clause_span_coverage.py --selftest
"""
import argparse
import hashlib
import os
import re
import sys
import time

FENCE = re.compile(r"```.*?```", re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# Some specs mark layer boundaries with a box-drawing rule rather than a
# markdown heading. These are structure, not prose: scanning them reports a
# guaranteed 0%-covered "gap" that no clause could ever legitimately quote.
DIVIDER = re.compile(r"^[═=\-_─—]{3,}\s*(.*?)\s*[═=\-_─—]{3,}$")
RULE = re.compile(r"^[═=\-_─—]{3,}$")
ROW = re.compile(r'^- \*\*([A-Z0-9]+-[A-Z]+-\d{3})\*\* — \*[^*]+\* ".*"$')


def _line_kind(line):
    """rule | banner (═══ Title ═══) | content."""
    if RULE.match(line):
        return "rule", ""
    d = DIVIDER.match(line)
    if d and d.group(1):
        return "banner", d.group(1).strip()
    return "content", line


def _is_banner_block(lines):
    """True for layer separators, in both the one-line and three-line forms.

    One-line:    ═══════ Reference Layer ═══════
    Three-line:  ═══════
                        ERROR SEMANTICS
                 ═══════
    Neither is prose; scanning them yields a guaranteed 0%-covered run that no
    clause could legitimately quote, which is pure noise in the gap count.
    """
    kinds = [_line_kind(l) for l in lines]
    if not any(k in ("rule", "banner") for k, _ in kinds):
        return None
    for k, v in kinds:
        if k == "content" and (len(v) >= 60 or v.endswith((".", ":", ";"))):
            return None
    titles = [v for _, v in kinds if v]
    return max(titles, key=len) if titles else ""


def norm(s):
    """Whitespace normalisation identical to verify_clauses.py."""
    return " ".join(s.split())


def self_md5():
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return "unknown"


def load_quotes(path):
    """Return [(clause_id, quote)] using verify_clauses.py's row grammar."""
    out, malformed = [], 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not re.match(r"^- \*\*[A-Z0-9]+-[A-Z]+-\d{3}\*\*", line):
                continue
            if not ROW.match(line):
                malformed += 1
                continue
            cid = re.match(r"^- \*\*([A-Z0-9]+-[A-Z]+-\d{3})\*\*", line).group(1)
            out.append((cid, line[line.index('"') + 1:line.rindex('"')]))
    return out, malformed


def prose_units(spec_text, section_re=None):
    """Split spec prose into units, dropping code fences and HTML comments.

    A unit is a blank-line-separated block, which makes each numbered invariant
    its own unit. Returns [(section, unit_text)].
    """
    text = HTML_COMMENT.sub("", spec_text)
    text = FENCE.sub("\n\n", text)

    units, section = [], "(preamble)"
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        banner = _is_banner_block(lines)
        if banner is not None:
            if banner:
                section = banner
            continue

        head = HEADING.match(block.splitlines()[0])
        if head:
            section = head.group(2).strip()
            rest = "\n".join(block.splitlines()[1:]).strip()
            if not rest:
                continue
            block = rest
        if section_re and not section_re.search(section):
            continue
        units.append((section, block))
    return units


def analyse(spec_path, clauses_path, section_re, min_run, oracle_dir):
    spec_text = open(spec_path, encoding="utf-8").read()
    quotes, malformed = load_quotes(clauses_path)

    # --- Gate 1 input: verbatim fraction against the FULL spec, so the number
    # is directly comparable to verify_clauses.py's own PASS count.
    full_norm = norm(spec_text)
    verbatim = [q for _, q in quotes if q in full_norm]
    frac = len(verbatim) / len(quotes) if quotes else 0.0

    # --- Build the normalised prose string with unit spans recorded.
    units = prose_units(spec_text, section_re)
    parts, spans = [], []
    cursor = 0
    for section, raw in units:
        n = norm(raw)
        if not n:
            continue
        if parts:
            cursor += 1  # the single space we join with
        parts.append(n)
        spans.append((section, cursor, cursor + len(n), n))
        cursor += len(n)
    prose = " ".join(parts)

    covered = bytearray(len(prose))
    used = set()
    for cid, q in quotes:
        if not q:
            continue
        i = prose.find(q)
        while i != -1:
            covered[i:i + len(q)] = b"\x01" * len(q)
            used.add(cid)
            i = prose.find(q, i + 1)

    results = []
    for section, s, e, n in spans:
        seg = covered[s:e]
        gaps, i = [], 0
        while i < len(seg):
            if not seg[i]:
                j = i
                while j < len(seg) and not seg[j]:
                    j += 1
                frag = n[i:j].strip()
                if len(frag) >= min_run:
                    gaps.append(frag)
                i = j
            else:
                i += 1
        pct = (100 * sum(seg) // len(seg)) if len(seg) else 100
        results.append((section, n, pct, gaps))

    oracle_terms = None
    if oracle_dir and os.path.isdir(oracle_dir):
        blob = []
        for root, _, files in os.walk(oracle_dir):
            for f in files:
                if f.endswith((".rs", ".py", ".go", ".ts", ".java")):
                    try:
                        blob.append(open(os.path.join(root, f),
                                         encoding="utf-8", errors="ignore").read())
                    except OSError:
                        pass
        oracle_terms = "\n".join(blob)

    return {
        "quotes": quotes, "malformed": malformed, "frac": frac,
        "unmatched": [c for c, q in quotes if q not in full_norm],
        "results": results, "used": used, "prose_len": len(prose),
        "covered": sum(covered), "oracle_terms": oracle_terms,
    }


def oracle_rank(gap, oracle_terms):
    """Does any code-span identifier in this uncovered run appear in the oracle?"""
    if oracle_terms is None:
        return None
    ids = re.findall(r"`([A-Za-z_][A-Za-z0-9_]{2,})", gap)
    hits = sorted({i for i in ids if re.search(r"\b%s\b" % re.escape(i), oracle_terms)})
    return hits


# An uncovered run that is only a list number and a bold label is a naming
# artefact, not unpinned behaviour: the clause quotes the invariant's body and
# skips its title. Counting those alongside real gaps is how a scan turns a
# tidy clause set into a scary number.
LABEL_ONLY = re.compile(r"^\d*\.?\s*\*\*[^*]+\*\*[\s.:]*$")


def classify(gap):
    return "label" if LABEL_ONLY.match(gap.strip()) else "prose"


def run(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?")
    ap.add_argument("clauses", nargs="?")
    ap.add_argument("--section", default=None,
                    help="only sections whose heading matches this regex")
    ap.add_argument("--min-run", type=int, default=25,
                    help="report uncovered runs of at least N chars (default 25)")
    ap.add_argument("--min-verbatim", type=float, default=0.95,
                    help="refuse to run below this verbatim fraction (default 0.95)")
    ap.add_argument("--oracle", default=None,
                    help="oracle dir; ranks gaps by whether a test references them")
    ap.add_argument("--quiet", action="store_true", help="summary lines only")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.spec or not args.clauses:
        ap.error("SPEC and CLAUSES are required (or use --selftest)")

    section_re = re.compile(args.section) if args.section else None
    a = analyse(args.spec, args.clauses, section_re, args.min_run, args.oracle)

    print(f"tool md5      : {self_md5()}")
    print(f"spec          : {args.spec}")
    print(f"clauses       : {args.clauses}")

    s_m, c_m = os.path.getmtime(args.spec), os.path.getmtime(args.clauses)
    fmt = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    print(f"spec mtime    : {fmt(s_m)}")
    print(f"clauses mtime : {fmt(c_m)}   (skew {c_m - s_m:+.0f}s)")
    if c_m < s_m:
        print("  !! clauses.md is OLDER than spec_v1.md — clause set may be stale;")
        print("     coverage gaps below may be artefacts of an unfinished edit.")

    print(f"clause rows   : {len(a['quotes'])}  (malformed {a['malformed']})")
    print(f"verbatim frac : {a['frac']:.3f}")
    if a["frac"] < args.min_verbatim:
        print()
        print(f"REFUSING TO REPORT: verbatim fraction {a['frac']:.3f} < "
              f"{args.min_verbatim:.2f}.")
        print("A substring instrument on a paraphrasing or stale clause set")
        print("manufactures findings. Fix the clause set, then re-run.")
        for cid in a["unmatched"][:10]:
            print(f"  unmatched: {cid}")
        return 2

    gapped = [r for r in a["results"] if r[3]]
    prose_gapped = [r for r in a["results"]
                    if any(classify(g) == "prose" for g in r[3])]
    n_label = sum(1 for r in a["results"] for g in r[3] if classify(g) == "label")
    n_prose = sum(1 for r in a["results"] for g in r[3] if classify(g) == "prose")
    total_pct = (100 * a["covered"] // a["prose_len"]) if a["prose_len"] else 100
    print(f"units scanned : {len(a['results'])}")
    print(f"span coverage : {total_pct}%  ({a['covered']}/{a['prose_len']} chars)")
    print(f"units w/ gaps : {len(gapped)}  ({len(prose_gapped)} with substantive prose)")
    print(f"gap runs      : {n_prose} prose, {n_label} label-only")
    print()

    if not args.quiet:
        for section, n, pct, gaps in a["results"]:
            real = [g for g in gaps if classify(g) == "prose"]
            if not real:
                continue
            title = re.match(r"(?:\d+\.\s*)?\*\*(.+?)\*\*", n)
            label = title.group(1) if title else n[:48]
            print(f"[GAP] {section} :: {label[:56]}  ({pct}% covered)")
            for g in real:
                hits = oracle_rank(g, a["oracle_terms"])
                tag = ""
                if hits:
                    tag = f"  <-- ORACLE REFERENCES {', '.join(hits[:4])}"
                elif hits == []:
                    tag = "  (no oracle reference)"
                print(f"       {g[:160]}{tag}")
            print()

    return 1 if prose_gapped else 0


SELFTEST_SPEC = """<!-- INTERNAL
provenance: seeded
-->
# Toy Spec

## Invariants

1. **Alpha holds**: the alpha property is preserved under every operation
   that the store performs on a reference name.

2. **Beta holds**: the beta property is preserved under concatenation, and
   this second sentence is deliberately left unquoted by any clause row so
   that the seeded gap has something to find.

```rust
pub fn declaration_should_be_ignored() {}
```
"""

SELFTEST_CLAUSES = """## TOY-INV — Invariants

- **TOY-INV-001** — *Alpha.* "**Alpha holds**: the alpha property is preserved under every operation that the store performs on a reference name."
- **TOY-INV-002** — *Beta.* "**Beta holds**: the beta property is preserved under concatenation"
"""


def selftest():
    """Negative control: seed a known uncovered span, prove the tool fires.

    A scan that has never caught its target has uninformative greens.
    """
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, "spec_v1.md")
        cl = os.path.join(d, "clauses.md")
        open(sp, "w").write(SELFTEST_SPEC)
        open(cl, "w").write(SELFTEST_CLAUSES)
        os.utime(cl, (time.time() + 5, time.time() + 5))

        a = analyse(sp, cl, re.compile("Invariants"), 25, None)

        seeded = [r for r in a["results"] if r[3]]
        print("case 1 — seeded gap must FIRE")
        if seeded:
            print(f"  PASS: {len(seeded)} unit(s) flagged")
            for _, _, _, gaps in seeded:
                for g in gaps:
                    print(f"    caught: {g[:90]}")
        else:
            print("  FAIL: seeded gap NOT detected")
            ok = False

        alpha = [r for r in a["results"] if "Alpha" in r[1]]
        print("case 2 — fully quoted unit must stay CLEAN")
        if alpha and not alpha[0][3]:
            print(f"  PASS: Alpha at {alpha[0][2]}% with no gap")
        else:
            print("  FAIL: false positive on a fully quoted unit")
            ok = False

        print("case 3 — declarations must be excluded from prose")
        if "declaration_should_be_ignored" not in " ".join(r[1] for r in a["results"]):
            print("  PASS: fenced code block not scanned")
        else:
            print("  FAIL: code block leaked into prose units")
            ok = False

        print("case 4 — sub-threshold verbatim fraction must REFUSE")
        open(cl, "w").write(SELFTEST_CLAUSES.replace(
            "the alpha property is preserved", "the ALPHA property was preserved"))
        os.utime(cl, (time.time() + 5, time.time() + 5))
        rc = run([sp, cl, "--section", "Invariants", "--quiet"])
        if rc == 2:
            print("  PASS: refused on stale clause set")
        else:
            print(f"  FAIL: ran anyway (rc={rc})")
            ok = False

    print()
    print(f"SELFTEST {'PASS' if ok else 'FAIL'}  (tool md5 {self_md5()})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
