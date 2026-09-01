#!/usr/bin/env python3
"""Compilation-isolated Java scorer.

The stock Java runner compiles the whole oracle as one unit against the candidate,
so a single divergent signature fails `test-compile` and zeroes every test in both
suites -- a 0% that carries no gap and cannot be told apart from a hard task.

This scorer compiles each oracle test file on its own (that file plus the shared
fixtures, against the candidate's classpath). A file that compiles has its tests
run; a file that does not has its `@Test` methods counted as failed. A signature
error is then contained to the test files that actually reference the broken
symbol, and files that do not still produce real pass/fail -- which is what lets a
partial delivery show an atomic rate, an integration rate, and a gap between them.

It does NOT change task difficulty. It changes only how a build failure is
attributed: from "every test failed" to "the tests that depend on the broken
symbol failed". The behaviour each surviving test checks is unchanged.

The scorer's own soundness is checked two ways by the caller: it must reproduce
the reference at 100% and the signature stub at 0%. A scorer that cannot tell
those apart is not measuring anything.

Usage (inside spec2repo-java:latest):
    java_isolated_score.py <oracle-dir> <candidate-workspace> <out.json>

<candidate-workspace> is a Maven project; its jar and compile classpath are taken
from `mvn install` + `dependency:build-classpath`.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

TEST = re.compile(r"@Test\b")
METHOD = re.compile(r"@Test\b[\s\S]*?\bvoid\s+(\w+)\s*\(")


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def candidate_classpath(workspace: Path, oracle: Path) -> tuple[str, str]:
    """(candidate_jar_and_deps, error). Installs the candidate, resolves the oracle's deps."""
    inst = run(["mvn", "-B", "-q", "-DskipTests", "install"], cwd=workspace)
    if inst.returncode != 0:
        tail = "\n".join(inst.stdout.splitlines()[-15:])
        return "", f"candidate mvn install failed:\n{tail}"
    # The oracle POM already declares the candidate coordinate plus javassist and
    # junit; resolving its classpath is the classpath the tests need.
    cp_file = oracle / "target" / "cp.txt"
    cp_file.parent.mkdir(parents=True, exist_ok=True)
    res = run(["mvn", "-B", "-q", "dependency:build-classpath",
               f"-Dmdep.outputFile={cp_file}"], cwd=oracle)
    if res.returncode != 0 or not cp_file.exists():
        tail = "\n".join(res.stdout.splitlines()[-15:])
        return "", f"oracle classpath resolution failed:\n{tail}"
    return cp_file.read_text().strip(), ""


def methods_in(path: Path) -> list[str]:
    return METHOD.findall(path.read_text(encoding="utf-8", errors="replace"))


def main(argv: list[str]) -> int:
    oracle = Path(argv[1])
    workspace = Path(argv[2])
    out = Path(argv[3])
    test_root = oracle / "src" / "test" / "java"
    fixtures = sorted((test_root / "fixtures").glob("*.java"))

    result = {"atomic": {"passed": 0, "total": 0}, "integration": {"passed": 0, "total": 0},
              "files": [], "error": None}

    cp, err = candidate_classpath(workspace, oracle)
    if err:
        # A candidate whose own core does not install cannot be scored at all: there
        # is no artifact for any test to compile against. This is a core-level
        # failure, distinct from a leaf-signature one, and isolation cannot rescue it.
        result["error"] = err
        # Still record the denominators so the reading is interpretable.
        for layer in ("atomic", "integration"):
            for f in sorted((test_root / layer).glob("*.java")):
                result[layer]["total"] += len(methods_in(f))
        out.write_text(json.dumps(result, indent=2))
        print(json.dumps({k: result[k] for k in ("atomic", "integration", "error")}))
        return 1

    build = oracle / "target" / "isolated"
    build.mkdir(parents=True, exist_ok=True)

    for layer in ("atomic", "integration"):
        for src in sorted((test_root / layer).glob("*.java")):
            methods = methods_in(src)
            result[layer]["total"] += len(methods)
            classes_dir = build / layer / src.stem
            classes_dir.mkdir(parents=True, exist_ok=True)
            javac = run(["javac", "-cp", f"{cp}", "-d", str(classes_dir),
                         *[str(p) for p in fixtures], str(src)])
            if javac.returncode != 0:
                result["files"].append({"file": f"{layer}/{src.name}", "compiled": False,
                                        "methods": len(methods), "passed": 0})
                continue
            launcher = run(["java", "-cp", f"{cp}:{classes_dir}",
                            "org.junit.platform.console.ConsoleLauncher",
                            "--disable-banner", "--details=none",
                            "--select-class", f"{layer}.{src.stem}"])
            m = re.search(r"(\d+) tests successful", launcher.stdout)
            passed = int(m.group(1)) if m else 0
            result[layer]["passed"] += passed
            result["files"].append({"file": f"{layer}/{src.name}", "compiled": True,
                                    "methods": len(methods), "passed": passed})

    a, i = result["atomic"], result["integration"]
    total_p = a["passed"] + i["passed"]
    total_t = a["total"] + i["total"]
    a_rate = a["passed"] / a["total"] if a["total"] else 0.0
    i_rate = i["passed"] / i["total"] if i["total"] else 0.0
    result["overall_rate"] = total_p / total_t if total_t else 0.0
    result["gap_pp"] = round(100 * (a_rate - i_rate), 1)
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps({"atomic": a, "integration": i,
                      "overall_rate": round(result["overall_rate"], 3),
                      "gap_pp": result["gap_pp"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
