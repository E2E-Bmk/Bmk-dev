#!/usr/bin/env python3
"""Static inventory of a Java candidate clone.

Reports, per repository: main-source non-blank LOC, file counts, test-file and
`@Test` counts, JUnit 4 vs 5 file split, and test-resource count. The JUnit split
matters because the oracle runner shells out to Surefire and a JUnit 4 suite needs
the vintage engine on the oracle classpath; the resource count is the first signal
of a golden-file-dominated suite, which candidate-selector rejects.

Counts only `*/src/main/java/**` and `*/src/test/java/**` so that generated
sources under `target/` and vendored trees are excluded by construction.
"""

from __future__ import annotations

import sys
from pathlib import Path


def nonblank(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def survey(root: Path) -> dict[str, object]:
    main = [p for p in root.rglob("*.java") if "/src/main/java/" in str(p)]
    test = [p for p in root.rglob("*.java") if "/src/test/java/" in str(p)]
    at_test = junit5 = junit4 = 0
    for p in test:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        at_test += text.count("@Test")
        if "org.junit.jupiter" in text:
            junit5 += 1
        if "import org.junit.Test;" in text:
            junit4 += 1
    resources = [p for p in root.rglob("*") if "/src/test/resources/" in str(p) and p.is_file()]
    builds = sorted(
        p.name for p in root.iterdir()
        if p.name in {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"}
    )
    return {
        "build": ",".join(builds) or "none",
        "main_loc": sum(nonblank(p) for p in main),
        "main_files": len(main),
        "test_files": len(test),
        "at_test": at_test,
        "junit5_files": junit5,
        "junit4_files": junit4,
        "test_resources": len(resources),
    }


def main(argv: list[str]) -> int:
    base = Path(argv[1])
    names = argv[2:] or sorted(p.name for p in base.iterdir() if p.is_dir())
    for name in names:
        root = base / name
        if not root.is_dir():
            print(f"{name:24s} MISSING")
            continue
        row = survey(root)
        print(
            f"{name:24s} build={row['build']:<8s} "
            f"main_loc={row['main_loc']:<7d} main_files={row['main_files']:<5d} "
            f"test_files={row['test_files']:<4d} at_test={row['at_test']:<5d} "
            f"junit5={row['junit5_files']:<4d} junit4={row['junit4_files']:<4d} "
            f"test_res={row['test_resources']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
