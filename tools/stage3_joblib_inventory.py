from __future__ import annotations

import ast
import argparse
import json
import tokenize
from pathlib import Path


REPO = Path(r"G:\research\01_agents\swe-e2e\repo-pool\joblib__joblib")

REWRITES = {
    ("joblib/test/test_hashing.py", "test_hash_methods"): ("test_hash_methods_public_rewrite", "Hashing"),
    ("joblib/test/test_hashing.py", "test_hash_numpy_arrays"): ("test_hash_numpy_arrays_public_rewrite", "Hashing"),
    ("joblib/test/test_hashing.py", "test_dict_hash"): ("test_dict_hash_public_rewrite", "Hashing"),
    ("joblib/test/test_hashing.py", "test_set_hash"): ("test_set_hash_public_rewrite", "Hashing"),
    ("joblib/test/test_hashing.py", "test_string"): ("test_string_hash_public_rewrite", "Hashing"),
    ("joblib/test/test_hashing.py", "test_wrong_hash_name"): ("test_wrong_hash_name_public_rewrite", "Error Semantics"),
    ("joblib/test/test_memory.py", "test_no_memory"): ("test_no_memory_public_rewrite", "Disk-Backed Function Caching"),
    ("joblib/test/test_memory.py", "test_memory_exception"): ("test_memory_exception_public_rewrite", "Error Semantics"),
    ("joblib/test/test_memory.py", "test_memory_ignore"): ("test_memory_ignore_public_rewrite", "Disk-Backed Function Caching"),
    ("joblib/test/test_memory.py", "test_check_call_in_cache"): ("test_check_call_in_cache_public_rewrite", "Disk-Backed Function Caching"),
    ("joblib/test/test_memory.py", "test_call_and_shelve"): ("test_call_and_shelve_public_rewrite", "Shelved Results"),
    ("joblib/test/test_numpy_pickle.py", "test_standard_types"): ("test_standard_types_public_rewrite", "Persistence And Compression"),
    ("joblib/test/test_numpy_pickle.py", "test_value_error"): ("test_dump_value_error_public_rewrite", "Error Semantics"),
    ("joblib/test/test_numpy_pickle.py", "test_pathlib"): ("test_pathlib_public_rewrite", "Persistence And Compression"),
}

CORE_FILES = {
    "joblib/test/test_hashing.py",
    "joblib/test/test_memory.py",
    "joblib/test/test_numpy_pickle.py",
    "joblib/test/test_numpy_pickle_compat.py",
    "joblib/test/test_numpy_pickle_utils.py",
    "joblib/test/test_store_backends.py",
}


def carriers() -> list[Path]:
    test_root = REPO / "joblib" / "test"
    files = sorted(test_root.glob("*.py"))
    files.extend(sorted((test_root / "data").glob("*.py")))
    files.extend(
        [REPO / "conftest.py", REPO / "doc" / "conftest.py", REPO / "joblib" / "testing.py"]
    )
    return sorted(files)


def dotted_imports(tree: ast.AST) -> list[str]:
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "." * node.level)
    return sorted(set(imports))


def test_functions(tree: ast.AST) -> list[dict[str, object]]:
    rows = []
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        names = sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name)})
        attrs = sorted({n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)})
        cls = None
        parent = parents.get(node)
        while parent is not None:
            if isinstance(parent, ast.ClassDef):
                cls = parent.name
                break
            parent = parents.get(parent)
        rows.append(
            {
                "name": node.name,
                "class": cls,
                "line": node.lineno,
                "names": names,
                "private_attrs": [x for x in attrs if x.startswith("_")],
            }
        )
    return sorted(rows, key=lambda row: int(row["line"]))


def inventory() -> list[dict[str, object]]:
    payload = []
    for path in carriers():
        with tokenize.open(path) as stream:
            source = stream.read()
        tree = ast.parse(source, filename=str(path))
        payload.append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "imports": dotted_imports(tree),
                "tests": test_functions(tree),
            }
        )
    return payload


def candidate_map(payload: list[dict[str, object]]) -> str:
    lines = [
        "# Candidate Filter Map",
        "",
        "Function accounting is over the 325 AST `test*` functions before parametrization. Rewrites are standalone public-API extractions in `rewritten_upstream_tests.py`; all other rows remain excluded from Track A scoring.",
        "",
        "| upstream_function | status | spec_section | rewritten_nodeid | evidence |",
        "|---|---|---|---|---|",
    ]
    kept = 0
    excluded = 0
    for carrier in payload:
        path = str(carrier["path"])
        for test in carrier["tests"]:
            name = str(test["name"])
            cls = test["class"]
            suffix = f"::{cls}::{name}" if cls else f"::{name}"
            upstream = f"{path}{suffix}"
            rewrite = REWRITES.get((path, name))
            if rewrite:
                kept += 1
                rewritten_name, section = rewrite
                lines.append(
                    f"| `{upstream}` | covered-rewrite | {section} | "
                    f"`filter/rewritten_upstream_tests.py::{rewritten_name}` | Same public contract; private/helper setup removed. |"
                )
                continue
            excluded += 1
            private_attrs = list(test["private_attrs"])
            if private_attrs:
                shown = ", ".join(f"`{item}`" for item in private_attrs[:4])
                reason = f"private assertion/access ({shown})"
                status = "excluded"
            elif path not in CORE_FILES:
                reason = "out-of-scope carrier or upstream testing/helper dependency"
                status = "excluded"
            else:
                reason = "carrier fixture/internal import dependency or implementation-shaped assertion; public rewrite attempt not retained"
                status = "source-only"
            lines.append(f"| `{upstream}` | {status} | - | - | {reason}. |")
    lines.extend(
        [
            "",
            f"Total functions: {kept + excluded} | kept rewrites: {kept} | excluded/source-only: {excluded}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-map", action="store_true")
    args = parser.parse_args()
    payload = inventory()
    if args.candidate_map:
        print(candidate_map(payload), end="")
        return
    print(json.dumps(payload, indent=2))
    print(f"CARRIERS={len(payload)}")
    print(f"TEST_FUNCTIONS={sum(len(row['tests']) for row in payload)}")


if __name__ == "__main__":
    main()
