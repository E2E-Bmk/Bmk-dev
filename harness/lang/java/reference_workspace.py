#!/usr/bin/env python3
"""Build a flattened single-module reference workspace for a Java task.

The scoring sandbox treats the workspace as the candidate's whole delivery: it
runs `mvn install` at the workspace root and then checks that the oracle's target
coordinate resolved to what that install produced. Two consequences shape this
script.

First, the workspace POM's own `artifactId` has to be the target artifact.
`JavaRunner.provenance` reads `{workspace}/pom.xml`, collects `artifactId` and
`groupId:artifactId` into an `own` set, and only reports the workspace as the
artifact's origin when the resolved coordinate is in that set. Handing it a
multi-module aggregator therefore fails the provenance audit even though the
install succeeded, because the aggregator's artifactId is not the target's.

Second, the module POM as it sits in the upstream tree is not self-contained: it
omits dependency versions and compiler settings that it inherits from the
aggregator's `dependencyManagement`. Copying the module directory alone yields a
build that cannot resolve its own dependencies.

So the workspace is synthesised from `help:effective-pom` output, which has every
inherited value already resolved. Only the parts a candidate would have to write
are kept -- coordinates, the compile-scope dependencies with concrete versions,
and the compiler release -- and the inherited release machinery (gpg, javadoc,
assembly, checkstyle, enforcer, source, bnd) is dropped. Keeping those would make
the reference gate fail on signing keys and network access that have nothing to
do with whether the oracle passes.

Usage:
    java_reference_workspace.py <effective-pom> <module-src-dir> <out-workspace>
      [--java-release N]

`<effective-pom>` is the output of
`mvn -pl <module> help:effective-pom -Doutput=<file>` run inside the image.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

POM_NS = "http://maven.apache.org/POM/4.0.0"

# Scopes whose dependencies belong to the delivered artifact. `test` is excluded
# because the oracle supplies its own test dependencies, and shipping the
# upstream test stack into the workspace would let a candidate's build resolve
# testing utilities the spec never mentions.
KEEP_SCOPES = {None, "", "compile", "runtime", "provided"}


def qn(tag: str) -> str:
    return f"{{{POM_NS}}}{tag}"


def text_of(parent: ET.Element, tag: str) -> str | None:
    node = parent.find(qn(tag))
    return node.text.strip() if node is not None and node.text else None


def extract(effective_pom: Path) -> dict[str, object]:
    # The default parser is used deliberately: the input is not third-party XML but
    # output this pipeline generated moments earlier by running `help:effective-pom`
    # against a pinned upstream checkout inside our own image. Python's ElementTree
    # already refuses external entity resolution; the residual entity-expansion
    # concern needs attacker-controlled input, which this path does not have.
    root = ET.parse(effective_pom).getroot()
    # The effective POM keeps a <parent> block while also stating the resolved
    # coordinates at top level; read the top-level ones and let the parent go.
    deps = []
    container = root.find(qn("dependencies"))
    if container is not None:
        for dep in container.findall(qn("dependency")):
            if text_of(dep, "scope") not in KEEP_SCOPES:
                continue
            if (text_of(dep, "optional") or "false").lower() == "true":
                continue
            group, artifact = text_of(dep, "groupId"), text_of(dep, "artifactId")
            version = text_of(dep, "version")
            if not (group and artifact and version):
                continue
            deps.append(
                {
                    "groupId": group,
                    "artifactId": artifact,
                    "version": version,
                    "scope": text_of(dep, "scope"),
                }
            )
    return {
        "groupId": text_of(root, "groupId"),
        "artifactId": text_of(root, "artifactId"),
        "version": text_of(root, "version"),
        "dependencies": deps,
    }


def render(meta: dict[str, object], release: str) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<project xmlns="http://maven.apache.org/POM/4.0.0"',
        '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0'
        ' http://maven.apache.org/xsd/maven-4.0.0.xsd">',
        "  <modelVersion>4.0.0</modelVersion>",
        f'  <groupId>{meta["groupId"]}</groupId>',
        f'  <artifactId>{meta["artifactId"]}</artifactId>',
        f'  <version>{meta["version"]}</version>',
        "  <packaging>jar</packaging>",
        "  <properties>",
        f"    <maven.compiler.release>{release}</maven.compiler.release>",
        "    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>",
        "  </properties>",
        "  <dependencies>",
    ]
    for dep in meta["dependencies"]:  # type: ignore[index]
        lines.append("    <dependency>")
        lines.append(f'      <groupId>{dep["groupId"]}</groupId>')
        lines.append(f'      <artifactId>{dep["artifactId"]}</artifactId>')
        lines.append(f'      <version>{dep["version"]}</version>')
        if dep["scope"]:
            lines.append(f'      <scope>{dep["scope"]}</scope>')
        lines.append("    </dependency>")
    lines += ["  </dependencies>", "</project>", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("effective_pom", type=Path)
    ap.add_argument("module_dir", type=Path, help="module root holding src/main/java")
    ap.add_argument("out", type=Path)
    ap.add_argument("--java-release", default="21")
    args = ap.parse_args(argv[1:])

    meta = extract(args.effective_pom)
    if not meta["artifactId"]:
        print("no artifactId in effective pom", file=sys.stderr)
        return 2

    main_src = args.module_dir / "src" / "main"
    if not main_src.is_dir():
        print(f"no src/main under {args.module_dir}", file=sys.stderr)
        return 2

    if args.out.exists():
        shutil.rmtree(args.out)
    (args.out / "src").mkdir(parents=True)
    shutil.copytree(main_src, args.out / "src" / "main")
    (args.out / "pom.xml").write_text(render(meta, args.java_release), encoding="utf-8")

    java_files = sum(1 for _ in (args.out / "src" / "main").rglob("*.java"))
    print(
        f'{meta["groupId"]}:{meta["artifactId"]}:{meta["version"]} '
        f'deps={len(meta["dependencies"])} java_files={java_files} -> {args.out}'
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
