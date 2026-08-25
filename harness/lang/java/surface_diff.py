#!/usr/bin/env python3
"""Diff a task's declared public surface against its reference implementation.

Rule 4 requires the reference implementation to pass the whole oracle. For a
statically-typed language that is not merely a pass-rate question: the oracle
compiles against the declared surface, so any member whose shape differs in the
reference makes the reference gate unreachable -- often unbuildable -- and the
divergence is discovered only after the oracle exists.

`Bmk-dev/harness/spec_stub_diff.py` performs this check for Rust by parsing the
spec's fenced blocks. It is Rust-specific throughout (`scan_rust`,
`parse_spec_rust_blocks`, `::` paths, derives), so Java needs its own instrument.

Java admits a stronger one than parsing markdown. The spec's surface stub is a
compilable transcription of the declared surface, and the reference is a
compilable implementation, so both can be handed to `javap` and compared on
compiler-resolved signatures rather than on text. What comes out is exactly the
set of members that would break the oracle link.

Two directions are reported, and they mean different things:

* **declared but divergent/absent in the reference** -- the reference cannot
  satisfy the oracle. Either the reference needs an adaptation delta, or the spec
  claims a shape upstream does not have.
* **present in the reference but not declared** -- harmless for the link, but it
  marks surface the candidate is not asked for, which is where accidental
  leakage of upstream internals into an oracle comes from.

Usage:
    java_surface_diff.py <declared-classes-dir> <reference-classes-dir> [--quiet-extra]

Both arguments are `target/classes` directories of built Maven projects. Run
inside the scoring image so `javap` is the same JDK the scorer uses.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# `javap` prefixes each member line with whitespace; the class header has none.
# Compiler-generated bridges and synthetic accessors are not part of the authored
# surface and would show up as spurious divergence.
_SYNTHETIC = re.compile(r"\baccess\$\d+|\bthis\$\d+|\bvalues\(\)|\bvalueOf\(")


def split_types(names: str) -> list[str]:
    """Split a comma-separated type list, ignoring commas inside generic arguments."""
    parts, depth, buf = [], 0, ""
    for char in names:
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(buf.strip())
            buf = ""
        else:
            buf += char
    if buf.strip():
        parts.append(buf.strip())
    return [p for p in parts if p]


def parse_header(header: str) -> tuple[str, str, list[str]]:
    """(prefix, superclass, interfaces) from a javap class header.

    Interfaces and the superclass are separated because they compare with opposite
    semantics. A reference that implements *more* interfaces than the spec declares
    still satisfies every oracle written against the declared surface -- the extra
    supertypes are unreachable from the declared API and harmless. A superclass
    with different type arguments is not harmless: `OutputGenerator<String>` and
    `OutputGenerator<XmlOutput>` give `generate()` incompatible return types, so an
    oracle expecting the former cannot compile against the latter.

    Comparing the header as one string conflates the two and reports the benign
    case as a blocker. That happened on three japicmp model types whose reference
    merely carries additional marker interfaces.
    """
    interfaces: list[str] = []
    match = re.search(r"\bimplements\s+([\w.$,<>\[\]\s]+)$", header)
    if match:
        interfaces = split_types(match.group(1))
        header = header[: match.start()].rstrip()
    else:
        # An interface declaration uses `extends` for its supertypes, which follow
        # subset semantics like `implements` does.
        match = re.search(r"\binterface\s+[\w.$]+.*?\bextends\s+([\w.$,<>\[\]\s]+)$", header)
        if match:
            interfaces = split_types(match.group(1))
            header = header[: match.start(1)].rstrip().removesuffix("extends").rstrip()

    superclass = ""
    match = re.search(r"\bclass\s+[\w.$<>,\[\]\s]+?\bextends\s+([\w.$<>,\[\]\s]+)$", header)
    if match:
        superclass = match.group(1).strip()
        header = header[: match.start()].rstrip()

    return header.strip(), superclass, sorted(interfaces)


def class_names(classes_dir: Path) -> list[str]:
    names = []
    for path in sorted(classes_dir.rglob("*.class")):
        rel = path.relative_to(classes_dir).with_suffix("")
        names.append(str(rel).replace("/", "."))
    return names


def javap_surface(classes_dir: Path, names: list[str]) -> tuple[dict[str, set[str]], dict[str, str]]:
    """({Class: {member, ...}}, {Class: raw header}) for public members."""
    if not names:
        return {}, {}
    # One javap invocation for the whole set: per-class spawning dominates runtime
    # on a surface of a few hundred types.
    proc = subprocess.run(
        ["javap", "-public", "-cp", str(classes_dir), *names],
        capture_output=True,
        text=True,
    )
    surface: dict[str, set[str]] = {}
    headers: dict[str, str] = {}
    current: str | None = None
    for line in proc.stdout.splitlines():
        if not line.strip() or line.strip() == "}":
            continue
        if not line.startswith(" "):
            # Class header, e.g. `public final class org.plumbline.model.JApiClass ... {`
            match = re.search(r"(?:class|interface|enum|record|@interface)\s+([\w.$]+)", line)
            if match:
                current = match.group(1)
                headers[current] = line.strip().rstrip("{").strip()
                surface.setdefault(current, set())
            continue
        if current is None:
            continue
        member = line.strip().rstrip(";")
        if _SYNTHETIC.search(member):
            continue
        surface[current].add(member)
    return surface, headers


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("declared", type=Path, help="target/classes of the surface stub")
    ap.add_argument("reference", type=Path, help="target/classes of the reference impl")
    ap.add_argument("--quiet-extra", action="store_true",
                    help="omit the reference-only report")
    args = ap.parse_args(argv[1:])

    for path in (args.declared, args.reference):
        if not path.is_dir():
            print(f"not a directory: {path}", file=sys.stderr)
            return 2

    declared, declared_headers = javap_surface(args.declared, class_names(args.declared))
    reference, reference_headers = javap_surface(args.reference, class_names(args.reference))

    missing_types = sorted(set(declared) - set(reference))
    divergent: list[tuple[str, str]] = []
    benign_supertypes: list[tuple[str, list[str]]] = []
    for name in sorted(set(declared) & set(reference)):
        for member in sorted(declared[name] - reference[name]):
            divergent.append((name, member))

        _, decl_super, decl_ifaces = parse_header(declared_headers.get(name, ""))
        _, ref_super, ref_ifaces = parse_header(reference_headers.get(name, ""))
        # Superclass: exact. Differing type arguments change inherited member
        # signatures, which is what breaks the oracle link.
        if decl_super and decl_super != ref_super:
            have = ref_super or "none"
            divergent.append(
                (name, f"SUPERCLASS declared '{decl_super}' but reference has '{have}'")
            )
        # Interfaces: subset. Extra supertypes in the reference are unreachable from
        # the declared API, so they cannot affect any oracle.
        undeclared_in_ref = sorted(set(decl_ifaces) - set(ref_ifaces))
        if undeclared_in_ref:
            divergent.append((name, "INTERFACES declared but absent from reference: "
                                    + ",".join(undeclared_in_ref)))
        extra_in_ref = sorted(set(ref_ifaces) - set(decl_ifaces))
        if extra_in_ref:
            benign_supertypes.append((name, extra_in_ref))

    print(f"declared types={len(declared)}  reference types={len(reference)}")
    print(f"declared members={sum(len(v) for v in declared.values())}")
    print()

    if missing_types:
        print(f"TYPES DECLARED BUT ABSENT FROM THE REFERENCE ({len(missing_types)}):")
        for name in missing_types:
            print(f"  {name}")
        print()

    if divergent:
        print(f"MEMBERS DECLARED BUT ABSENT OR DIFFERENTLY SHAPED IN THE REFERENCE "
              f"({len(divergent)}):")
        by_type: dict[str, list[str]] = {}
        for name, member in divergent:
            by_type.setdefault(name, []).append(member)
        for name in sorted(by_type):
            print(f"  {name}")
            for member in by_type[name]:
                print(f"      {member}")
        print()

    if not args.quiet_extra:
        if benign_supertypes:
            print(f"reference carries supertypes the spec does not declare "
                  f"({len(benign_supertypes)} types) -- NOT blockers, the declared API "
                  f"cannot reach them:")
            for name, extra in benign_supertypes[:15]:
                print(f"  {name}: {','.join(extra)}")
            if len(benign_supertypes) > 15:
                print(f"  ... {len(benign_supertypes) - 15} more")
            print()
        extra_types = sorted(set(reference) - set(declared))
        if extra_types:
            print(f"types present in the reference but not declared ({len(extra_types)}) "
                  f"-- harmless for the oracle link, but not the candidate's job:")
            for name in extra_types[:30]:
                print(f"  {name}")
            if len(extra_types) > 30:
                print(f"  ... {len(extra_types) - 30} more")
            print()

    blocking = len(missing_types) + len(divergent)
    print(f"REFERENCE-GATE BLOCKERS: {blocking}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
