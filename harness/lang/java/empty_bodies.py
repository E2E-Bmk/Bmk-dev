#!/usr/bin/env python3
"""Build a behaviour-empty stub: keep every declaration, empty every method body.
Brace-matched so generics/lambdas/nested classes don't fool it. Abstract/interface
methods (no body) are left alone. Default returns by declared return type.
Result must compile (all symbols present) yet pass zero oracle tests.
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) / "src" / "main" / "java"

# signature just before a body `{`: modifiers, return type, name, params, optional throws
SIG = re.compile(
    r'(?P<indent>[ \t]*)(?P<head>(?:(?:public|private|protected|static|final|abstract|'
    r'synchronized|native|default|strictfp)\s+)*'
    r'(?P<ret>[\w.$<>\[\],?\s&]+?)\s+(?P<name>\w+)\s*\([^;{}]*\)\s*(?:throws\s[\w.,\s]+?)?)\s*\{'
)
CTRL = {"if", "for", "while", "switch", "catch", "synchronized", "return", "new", "else", "do", "try"}
MODS = {"public", "private", "protected", "static", "final", "abstract", "synchronized",
        "native", "default", "strictfp", "volatile", "transient"}


def default_for(ret: str) -> str:
    # `throw` is valid in a method of any return type (including void), so it
    # sidesteps every type-mismatch a typed default would hit, and is the
    # canonical behaviour-empty body: reaches call phase, fails semantically.
    return "throw new UnsupportedOperationException();"


def empty_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    out = []
    i = 0
    n = len(text)
    count = 0
    while i < n:
        m = SIG.match(text, i) if False else None
        m = SIG.search(text, i)
        if not m:
            out.append(text[i:])
            break
        name = m.group("name")
        # skip control keywords, and constructors mis-parsed as ret=<modifier>
        if name in CTRL or m.group("ret").strip() in CTRL or m.group("ret").strip() in MODS:
            out.append(text[i:m.end()])
            i = m.end()
            continue
        # find the matching close brace for the body opened at m.end()-1
        depth = 1
        j = m.end()
        while j < n and depth:
            c = text[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            j += 1
        # emit up to the sig, then an emptied body
        out.append(text[i:m.start()])
        body = default_for(m.group("ret"))
        out.append(f"{m.group('indent')}{m.group('head').strip()} {{ {body} }}")
        i = j
        count += 1
    path.write_text("".join(out), encoding="utf-8")
    return count


total = 0
FILTER = sys.argv[2] if len(sys.argv) > 2 else None
for jf in ROOT.rglob("*.java"):
    if FILTER and FILTER not in str(jf):
        continue
    total += empty_file(jf)
print("emptied methods:", total, "filter:", FILTER)
