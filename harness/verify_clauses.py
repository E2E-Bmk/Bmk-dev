#!/usr/bin/env python3
"""Verify that every quoted clause in clauses.md appears verbatim in spec_v1.md.

Method: collapse every run of whitespace (including newlines) in spec_v1.md to a
single space, then do a literal (non-regex) substring search for each quote.
"""
import re
import sys

SPEC = "/root/research/Bmk-dev/wip/gix-ref-peel-001/spec/spec_v1.md"
CLAUSES = "/root/research/Bmk-dev/wip/gix-ref-peel-001/spec/clauses.md"

# Optional positional arguments: <spec_v1.md> <clauses.md>. The clause-ID family
# is read off the clauses file rather than hard-coded, so the same checker works
# for any task's prefix (GIXREF-, GUPPY-, ...).
if len(sys.argv) > 1:
    SPEC = sys.argv[1]
if len(sys.argv) > 2:
    CLAUSES = sys.argv[2]

with open(CLAUSES, encoding="utf-8") as fh:
    _families = re.findall(r'^- \*\*([A-Z0-9]+)-[A-Z]+-\d{3}\*\*', fh.read(), re.M)
if not _families:
    sys.exit(f"no clause rows found in {CLAUSES}")
FAMILY = _families[0]

ROW = re.compile(r'^- \*\*(' + FAMILY + r'-[A-Z]+-\d{3})\*\* — \*[^*]+\* ".*"$')

with open(SPEC, encoding="utf-8") as fh:
    spec_norm = " ".join(fh.read().split())

rows, malformed = [], []
with open(CLAUSES, encoding="utf-8") as fh:
    for lineno, line in enumerate(fh, 1):
        line = line.rstrip("\n")
        if not line.startswith("- **" + FAMILY + "-"):
            continue
        m = ROW.match(line)
        if not m:
            malformed.append((lineno, line))
            continue
        cid = m.group(1)
        # quote = text between the FIRST and the LAST double quote on the line,
        # so quotes that themselves contain `"` survive intact.
        quote = line[line.index('"') + 1:line.rindex('"')]
        rows.append((lineno, cid, quote))

passed = [r for r in rows if r[2] in spec_norm]          # literal substring test
failed = [r for r in rows if r[2] not in spec_norm]

seen, dupes = set(), []
for _, cid, _ in rows:
    if cid in seen:
        dupes.append(cid)
    seen.add(cid)

# per-prefix counts
counts = {}
for _, cid, _ in rows:
    prefix = cid.rsplit("-", 1)[0]
    counts[prefix] = counts.get(prefix, 0) + 1

print(f"clauses parsed : {len(rows)}")
print(f"verbatim PASS  : {len(passed)}")
print(f"verbatim FAIL  : {len(failed)}")
print(f"malformed rows : {len(malformed)}")
print(f"duplicate IDs  : {len(dupes)}")
print()
print("per-prefix counts:")
for prefix in sorted(counts):
    print(f"  {prefix:<14} {counts[prefix]:>3}")

if malformed:
    print("\nMALFORMED:")
    for lineno, line in malformed:
        print(f"  line {lineno}: {line[:120]}")
if dupes:
    print("\nDUPLICATE IDS: " + ", ".join(dupes))
if failed:
    print("\nFAILING QUOTES:")
    for lineno, cid, quote in failed:
        print(f"  line {lineno} {cid}: {quote[:160]}")

sys.exit(1 if (failed or malformed or dupes) else 0)
