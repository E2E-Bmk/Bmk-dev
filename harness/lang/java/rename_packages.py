#!/usr/bin/env python3
"""Rewrite a reference workspace's package root, for de-identified tasks.

Every task in this round hands the candidate a renamed library: the spec describes
`org.plumbline`, never `japicmp`, so that a model cannot deliver by recalling the
upstream artifact's API paths. The consequence is that the reference
implementation can no longer be the upstream tree as it stands -- the oracle's
`import org.plumbline.cmp.JarArchiveComparator` does not resolve against source
that still declares `package japicmp.cmp`, so the reference gate can never reach
100% and Rule 4 has no evidence.

This rewrites a workspace produced by `java_reference_workspace.py` from the
upstream root to the task's root, and rewrites the POM coordinates to match.

Why the replacement is token-aware rather than a global text substitution
-----------------------------------------------------------------------

A blanket `sed s/japicmp/org.plumbline/g` also rewrites string literals and
comments. That matters because behaviour can depend on a literal: a resource
path, an XSLT template name, a message the oracle asserts on. Silently changing
those turns the reference into something that fails its own oracle for reasons
unrelated to the rename, and the failure surfaces far from its cause.

So substitution is confined to the three positions where the root is a package
reference: the `package` declaration, `import` statements, and dotted qualified
names in code. Occurrences inside string literals are counted and reported, never
changed -- they need a human decision, and this prints them so the decision is
made rather than skipped.

Usage:
    java_rename_packages.py <workspace> --from japicmp --to org.plumbline \\
        [--coordinates org.plumbline:plumbline-core:1.0.0] [--apply]

Without `--apply` it reports what would change and exits 0, which is how the
string-literal report is meant to be read first.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# A Java string literal, so its contents can be excluded from rewriting. Escaped
# quotes are handled; the pattern is deliberately not trying to parse comments,
# which are reported through the same channel because a stale comment is
# cosmetic while a stale literal is behavioural.
_STRING_LITERAL = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def _mask_literals(text: str) -> tuple[str, list[str]]:
    """Replace string literals with placeholders so rewrites cannot reach them."""
    stash: list[str] = []

    def take(match: re.Match[str]) -> str:
        stash.append(match.group(0))
        return f"\x00LIT{len(stash) - 1}\x00"

    return _STRING_LITERAL.sub(take, text), stash


def _restore_literals(text: str, stash: list[str]) -> str:
    for index, literal in enumerate(stash):
        text = text.replace(f"\x00LIT{index}\x00", literal)
    return text


def rewrite_source(
    text: str,
    old_root: str,
    new_root: str,
    type_renames: dict[str, str] | None = None,
) -> tuple[str, int, int]:
    """Returns (rewritten, replacements_made, occurrences_left_in_literals)."""
    masked, stash = _mask_literals(text)

    # `\b<old>\.` matches the root only where it heads a qualified name, which
    # covers the package declaration of a sub-package, imports and inline
    # qualified references in one rule.
    pattern = re.compile(rf"\b{re.escape(old_root)}\.")
    masked, count = pattern.subn(f"{new_root}.", masked)

    # A class sitting directly in the root package declares `package <old>;` with
    # no trailing dot, so the rule above cannot see it. Missing this leaves the
    # file's declaration pointing at the old root while the directory move puts it
    # under the new one, and javac reports `duplicate class: <old>.<Class>` --
    # which reads like a source defect rather than an incomplete rename.
    # japicmp has exactly one such file (`JApiCmp.java`), enough to fail the whole
    # build.
    bare = re.compile(rf"^(\s*(?:package|import)\s+(?:static\s+)?){re.escape(old_root)}\s*;", re.M)
    masked, bare_count = bare.subn(rf"\g<1>{new_root};", masked)
    count += bare_count

    # Type names carry the upstream brand too, and renaming only the package leaves
    # them behind. `java_surface_diff` on japicmp found the declared surface wanting
    # `JApiCompareException` while the renamed reference still offered
    # `JApiCmpException` -- a reference-gate blocker that no amount of package
    # rewriting fixes. Whole-word so `JApiCmpException` cannot also rewrite a
    # longer identifier that merely contains it.
    for old_type, new_type in (type_renames or {}).items():
        masked, type_count = re.subn(rf"\b{re.escape(old_type)}\b", new_type, masked)
        count += type_count

    in_literals = sum(literal.count(old_root) for literal in stash)
    return _restore_literals(masked, stash), count, in_literals


def rewrite_pom(text: str, coordinates: str | None) -> str:
    if not coordinates:
        return text
    group, artifact, version = coordinates.split(":", 2)
    text = re.sub(r"<groupId>[^<]*</groupId>", f"<groupId>{group}</groupId>", text, count=1)
    text = re.sub(
        r"<artifactId>[^<]*</artifactId>", f"<artifactId>{artifact}</artifactId>", text, count=1
    )
    text = re.sub(r"<version>[^<]*</version>", f"<version>{version}</version>", text, count=1)
    return text


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", type=Path)
    ap.add_argument("--from", dest="old_root", required=True, help="e.g. japicmp")
    ap.add_argument("--to", dest="new_root", required=True, help="e.g. org.plumbline")
    ap.add_argument("--coordinates", help="groupId:artifactId:version for the POM")
    ap.add_argument("--rename-type", action="append", default=[], metavar="Old=New",
                    help="rename a branded type name; repeatable")
    ap.add_argument("--apply", action="store_true", help="write changes; otherwise dry run")
    args = ap.parse_args(argv[1:])

    type_renames: dict[str, str] = {}
    for pair in args.rename_type:
        if "=" not in pair:
            print(f"--rename-type expects Old=New, got {pair!r}", file=sys.stderr)
            return 2
        old, new = pair.split("=", 1)
        type_renames[old.strip()] = new.strip()

    java_root = args.workspace / "src" / "main" / "java"
    if not java_root.is_dir():
        print(f"no src/main/java under {args.workspace}", file=sys.stderr)
        return 2

    sources = sorted(java_root.rglob("*.java"))
    total_replacements = 0
    literal_hits: list[tuple[Path, int]] = []
    rewritten: dict[Path, str] = {}

    for source in sources:
        text = source.read_text(encoding="utf-8-sig", errors="replace")
        new_text, count, in_literals = rewrite_source(
            text, args.old_root, args.new_root, type_renames
        )
        total_replacements += count
        if in_literals:
            literal_hits.append((source, in_literals))
        if count:
            rewritten[source] = new_text

    print(
        f"{len(sources)} sources, {total_replacements} qualified-name replacements, "
        f"{len(rewritten)} files touched"
    )
    if literal_hits:
        print(
            f"\n{sum(n for _, n in literal_hits)} occurrences of '{args.old_root}' remain inside "
            f"string literals in {len(literal_hits)} files. These are NOT rewritten -- a literal "
            f"can carry behaviour the oracle asserts on. Review:"
        )
        for path, count in literal_hits[:20]:
            print(f"  {count:3d}  {path.relative_to(args.workspace)}")
        if len(literal_hits) > 20:
            print(f"  ... {len(literal_hits) - 20} more files")

    if not args.apply:
        print("\ndry run; pass --apply to write")
        return 0

    for source, new_text in rewritten.items():
        source.write_text(new_text, encoding="utf-8")

    # A renamed type must also be renamed on disk: javac requires a public type's
    # file to be named after it.
    for old_type, new_type in type_renames.items():
        for path in sorted(java_root.rglob(f"{old_type}.java")):
            target = path.with_name(f"{new_type}.java")
            shutil.move(str(path), str(target))
            print(f"renamed {path.name} -> {target.name}")

    # Move the tree so the directory layout matches the new package declarations,
    # which javac requires.
    old_dir = java_root / Path(*args.old_root.split("."))
    new_dir = java_root / Path(*args.new_root.split("."))
    if old_dir.is_dir():
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        if new_dir.exists():
            shutil.rmtree(new_dir)
        shutil.move(str(old_dir), str(new_dir))
        # Drop now-empty ancestors of the old root.
        parent = old_dir.parent
        while parent != java_root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
        print(f"moved {old_dir.relative_to(java_root)} -> {new_dir.relative_to(java_root)}")

    pom = args.workspace / "pom.xml"
    if pom.is_file() and args.coordinates:
        pom.write_text(
            rewrite_pom(pom.read_text(encoding="utf-8"), args.coordinates), encoding="utf-8"
        )
        print(f"pom coordinates -> {args.coordinates}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
