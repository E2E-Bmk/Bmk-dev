#!/usr/bin/env python3
"""Strip the target package from a per-task AGENT image.

Mirrors the scoring sandbox exactly:
  1. uninstall the named reference DISTRIBUTIONS (e.g. dbt-core) while keeping
     sibling infrastructure that shares a namespace (e.g. dbt-duckdb);
  2. verify the target IMPORT names no longer resolve to real module code.
     A residual empty namespace package (origin=None, no __init__.py) is
     acceptable - that is exactly what the scoring container sees before the
     candidate installs.

Usage:
    python uninstall_targets.py --dists dbt-core -- dbt
    python uninstall_targets.py -- vcr          (verify only, nothing to uninstall)
"""
import argparse
import subprocess
import sys
import importlib.util


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dists", nargs="*", default=[],
                    help="distribution names to pip-uninstall")
    ap.add_argument("imports", nargs="*",
                    help="import names that must not resolve to real code")
    args = ap.parse_args()

    if args.dists:
        print(f"uninstall_targets: removing distributions {args.dists}")
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", *args.dists],
            check=False,  # absent distribution is fine
        )

    bad = []
    for imp in args.imports:
        spec = importlib.util.find_spec(imp)
        if spec is None:
            continue  # fully gone
        if spec.origin is None and not spec.submodule_search_locations:
            continue
        if spec.origin is None:
            # namespace package: acceptable only if no __init__.py anywhere
            import pathlib
            has_real_pkg = any(
                (pathlib.Path(p) / "__init__.py").exists()
                for p in spec.submodule_search_locations or []
            )
            if has_real_pkg:
                bad.append(f"{imp} (namespace with __init__.py at {list(spec.submodule_search_locations)})")
            else:
                print(f"uninstall_targets: {imp} leaves an empty namespace - ok")
            continue
        bad.append(f"{imp} -> {spec.origin}")

    if bad:
        print(f"uninstall_targets: TARGET STILL RESOLVES: {bad}")
        return 1
    print("uninstall_targets: target imports clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
