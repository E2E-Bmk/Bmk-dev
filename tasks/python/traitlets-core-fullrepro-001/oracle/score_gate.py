from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import warnings
from pathlib import Path

GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
ROOT_MAP = json.loads((GATE / "ROOT-MAP.json").read_text(encoding="utf-8"))
GATE_INPUTS = (
    "SPEC.md", "TASK.md", "ENVIRONMENT-CONTRACT.md", "ANCHOR-ADMISSION-PREREG.md", "ROOT-MAP.json", "MUTATION-PORTFOLIO.json", "SCORER-CONFIG.json",
    "RUNTIME-IDENTITY.json", "run_root.py", "score_gate.py", "reference-overlay/traitlets_v6_workspace.py",
    "reference-overlay/traitlets_v6_controls.py", "clean-api-scaffold/traitlets_v6_scaffold.py", "tests/workspace_support.py",
    "tests/test_native_controls.py", "tests/test_workspace_atomic.py", "tests/test_workspace_integration.py", "tests/test_workspace_system.py",
    "dummy/traitlets/__init__.py", "dummy/traitlets/workspace.py", "shallow-source-blank/traitlets/__init__.py",
    "shallow-source-blank/traitlets/workspace.py",
    "probe_source_blank.py", "finalize_gate.py",
)


def sha256_tree(root):
    digest = hashlib.sha256(); ignored = {".git", "__pycache__", ".pytest_cache", ".tmp"}
    files = sorted(path for path in Path(root).rglob("*") if path.is_file() and not ignored.intersection(path.relative_to(root).parts))
    for path in files:
        relative = path.relative_to(root).as_posix().encode(); data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative); digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def gate_input_sha256():
    digest = hashlib.sha256()
    for name in GATE_INPUTS:
        data = (GATE / name).read_bytes(); encoded = name.encode()
        digest.update(len(encoded).to_bytes(8, "big")); digest.update(encoded); digest.update(len(data).to_bytes(8, "big")); digest.update(data)
    return digest.hexdigest()


def inside(path, root):
    try: Path(path).resolve().relative_to(Path(root).resolve()); return True
    except ValueError: return False


def literal_version(path):
    try: tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except Exception: return None
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "__version__" for target in targets):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str): return node.value.value
    return None


def runtime_identity_probe():
    errors = []; identity = json.loads((GATE / CONFIG["declared_runtime_identity"]).read_text(encoding="utf-8"))
    runtime_site = (GATE / identity["runtime_site"]).resolve(); package = runtime_site / "traitlets"; version_file = package / "_version.py"
    tree_hash = sha256_tree(runtime_site); version_hash = hashlib.sha256(version_file.read_bytes()).hexdigest() if version_file.is_file() else None
    files = [path for path in runtime_site.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    marker = literal_version(version_file)
    if identity.get("case") != CONFIG["case"]: errors.append("runtime case mismatch")
    if tree_hash != identity.get("runtime_tree_sha256"): errors.append("runtime tree hash mismatch")
    if version_hash != identity.get("version_file_sha256") or marker != identity.get("version"): errors.append("runtime version marker mismatch")
    if len(files) != identity.get("file_count"): errors.append("runtime file count mismatch")
    code = ("import json,pathlib,sys;" + f"sys.path[:0]={[str(runtime_site)]!r};" +
            "import traitlets,traitlets._version;print(json.dumps({'version':traitlets.__version__,'traitlets':str(pathlib.Path(traitlets.__file__).resolve()),'_version':str(pathlib.Path(traitlets._version.__file__).resolve()),'search':[str(pathlib.Path(x).resolve()) for x in traitlets.__path__]},sort_keys=True))")
    child = subprocess.run([sys.executable, "-X", "utf8", "-B", "-I", "-c", code], text=True, encoding="utf-8", errors="replace", capture_output=True)
    imported = {}
    if child.returncode:
        errors.append("isolated runtime import failed")
    else:
        try: imported = json.loads(child.stdout)
        except json.JSONDecodeError: errors.append("runtime receipt malformed")
    if imported:
        if imported.get("version") != identity.get("version"): errors.append("imported runtime version mismatch")
        if not inside(imported.get("traitlets", ""), package) or not inside(imported.get("_version", ""), package): errors.append("runtime import origin escaped")
        if imported.get("search") != [str(package)]: errors.append("runtime search path not closed")
    return {"schema":"spec2repo.runtime-identity-probe.v1", "valid":not errors, "declared_version":identity.get("version"),
            "literal_version":marker, "version_file_sha256":version_hash, "runtime_tree_sha256":tree_hash,
            "runtime_file_count":len(files), "imported":imported, "returncode":child.returncode, "stderr":child.stderr, "errors":errors}


def rows(): return list(ROOT_MAP["roots"])


def module_for(root_id):
    native = {*(f"A{i:02d}" for i in range(1, 9)), *(f"I{i:02d}" for i in range(1, 5)), "S01", "S02"}
    if root_id in native: return "test_native_controls.py"
    if root_id.startswith("A"): return "test_workspace_atomic.py"
    if root_id.startswith("I"): return "test_workspace_integration.py"
    return "test_workspace_system.py"


def static_inventory():
    expected = [*(f"A{i:02d}" for i in range(1,17)), *(f"I{i:02d}" for i in range(1,25)), *(f"S{i:02d}" for i in range(1,9))]
    ids = [row["id"] for row in rows()]; errors = []
    if ids != expected: errors.append("root inventory differs from 16A+24I+8S")
    for root_id in ids:
        path = GATE / "tests" / module_for(root_id); tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}; function = functions.get(f"test_{root_id.lower()}")
        if function is None: errors.append(f"missing root {root_id}"); continue
        names = [item.arg for item in [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]]
        if names != ["tmp_path"] or function.args.vararg or function.args.kwarg or function.decorator_list: errors.append(f"invalid root signature {root_id}")
    portfolio = json.loads((GATE / "MUTATION-PORTFOLIO.json").read_text(encoding="utf-8"))
    mutation = {row["id"] for row in rows() if row["class"] == "mutation"}; declared = {root for family in portfolio["families"].values() for root in family["roots"]}
    if mutation != declared or len(mutation) != 34 or len(ids) - len(mutation) != 14: errors.append("mutation/native partition mismatch")
    dependencies = {dep for row in rows() for dep in row.get("depends_on", ())}
    if not dependencies.issubset(ids): errors.append("unknown dependency root")
    return ids, errors


def candidate_policy_errors(candidate, profile):
    errors = []; reference = Path(CONFIG["reference_package_root"]).resolve(); dummy = (GATE / "dummy").resolve()
    if not candidate.is_dir() or not (candidate / "traitlets" / "__init__.py").is_file(): return ["candidate lacks traitlets/__init__.py"]
    if profile in {"reference", "clean", "broad-eager", "broad-delivery-blind"} and candidate != reference: errors.append("profile requires pinned reference package")
    if profile == "dummy" and candidate != dummy: errors.append("dummy requires sealed root")
    if profile == "shallow" and candidate != (GATE / "shallow-source-blank").resolve(): errors.append("shallow requires sealed root")
    if profile in {"anchor", "arbitrary"} and candidate in {reference, dummy}: errors.append("independent candidate required")
    for path in candidate.rglob("*"):
        if path.is_symlink(): errors.append(f"candidate symlink forbidden: {path}")
        elif path.suffix == ".py":
            try:
                with warnings.catch_warnings(): warnings.simplefilter("ignore", SyntaxWarning); ast.parse(path.read_text(encoding="utf-8"))
            except Exception as exc: errors.append(f"invalid candidate source {path}: {exc}")
    return errors


def rate(passed, total): return round(passed / total, 8) if total else None
def metric(results, ids):
    selected = [item for item in results if item["root"] in ids]; passed = sum(item.get("passed") is True for item in selected)
    return {"passed":passed, "total":len(selected), "rate":rate(passed, len(selected))}


def score(results):
    atomic_ids = {row["id"] for row in rows() if row["kind"] == "atomic"}; integration_ids = {row["id"] for row in rows() if row["kind"] == "integration"}
    system_ids = {row["id"] for row in rows() if row["kind"] == "system"}; composition_ids = integration_ids | system_ids
    mutation_ids = {row["id"] for row in rows() if row["class"] == "mutation"}; all_ids = atomic_ids | composition_ids; native_ids = all_ids - mutation_ids
    passed_ids = {item["root"] for item in results if item.get("passed") is True}
    conditional = {row["id"] for row in rows() if row["kind"] != "atomic" and set(row.get("depends_on", ())).issubset(passed_ids)}
    atomic, composition = metric(results, atomic_ids), metric(results, composition_ids)
    families = sorted({row.get("family") for row in rows() if row.get("family")})
    return {"all_roots":metric(results, all_ids), "atomic":atomic, "composition":composition, "integration":metric(results,integration_ids),
            "system_e2e":metric(results,system_ids), "combined_rate":metric(results,all_ids)["rate"],
            "gap":round(atomic["rate"]-composition["rate"],8) if atomic["rate"] is not None and composition["rate"] is not None else None,
            "conditional_composition":metric(results,conditional),
            "adjusted_gap":round(atomic["rate"]-metric(results,conditional)["rate"],8) if conditional and atomic["rate"] is not None and metric(results,conditional)["rate"] is not None else None,
            "mutation_designated":metric(results,mutation_ids), "native_controls":metric(results,native_ids),
            "mutation_families":{family:metric(results,{row["id"] for row in rows() if row.get("family")==family}) for family in families}}


def git_fact(repository, *args):
    child = subprocess.run([CONFIG["git_executable"], "-c", f"safe.directory={repository}", "-C", str(repository), *args], text=True, encoding="utf-8", errors="replace", capture_output=True)
    return child.stdout.strip() if child.returncode == 0 else None


def run(candidate, profile, mode, only):
    started = time.time(); candidate = candidate.resolve(); inventory, invalid = static_inventory(); invalid.extend(candidate_policy_errors(candidate, profile))
    runtime = runtime_identity_probe(); invalid.extend(f"runtime identity: {item}" for item in runtime.get("errors", ()))
    order = list(inventory)
    if mode == "reverse": order.reverse()
    elif mode == "permuted": random.Random(CONFIG["permutation_seed"]).shuffle(order)
    if only: order = [only]; invalid.extend([] if only in inventory else [f"unknown root {only}"])
    tree_before = sha256_tree(candidate) if candidate.is_dir() else None; repository = Path(CONFIG["reference_repository_root"]).resolve()
    reference_before = {"commit":git_fact(repository,"rev-parse","HEAD"), "tree":git_fact(repository,"rev-parse","HEAD^{tree}"), "status":git_fact(repository,"status","--porcelain=v1","--untracked-files=all")}
    if reference_before != {"commit":CONFIG["reference_commit"],"tree":CONFIG["reference_tree"],"status":""}: invalid.append("pinned reference provenance mismatch")
    results = []
    if not invalid:
        env = dict(os.environ); env["PYTHONPATH"] = os.pathsep.join((str(GATE / "runtime-site"), CONFIG["dependency_site"])); env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        for root_id in order:
            try:
                child = subprocess.run([sys.executable, str(GATE / "run_root.py"), root_id, str(candidate), profile], cwd=GATE, env=env,
                                       text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=CONFIG["root_timeout_seconds"])
            except subprocess.TimeoutExpired as exc:
                invalid.append(f"root timeout {root_id}"); results.append({"root":root_id,"valid":False,"timeout":True}); continue
            try: record = json.loads(child.stdout)
            except json.JSONDecodeError: record = {"root":root_id,"valid":False,"stdout":child.stdout,"stderr":child.stderr}
            if child.returncode or record.get("root") != root_id or record.get("valid") is not True or record.get("phase") != "call": invalid.append(f"invalid root receipt {root_id}")
            results.append(record)
    tree_after = sha256_tree(candidate) if candidate.is_dir() else None
    if tree_before != tree_after: invalid.append("candidate tree changed")
    reference_after = {"commit":git_fact(repository,"rev-parse","HEAD"), "tree":git_fact(repository,"rev-parse","HEAD^{tree}"), "status":git_fact(repository,"status","--porcelain=v1","--untracked-files=all")}
    if reference_before != reference_after: invalid.append("reference provenance changed")
    return {"schema":"spec2repo.score-receipt.v3", "case":CONFIG["case"], "constitution":CONFIG["constitution"], "gate_input_sha256":gate_input_sha256(),
            "candidate":str(candidate), "candidate_profile":profile, "candidate_tree_sha256_before":tree_before, "candidate_tree_sha256_after":tree_after,
            "reference_before":reference_before, "reference_after":reference_after, "mode":mode, "only":only, "runtime_identity":runtime,
            "valid":not invalid and len(results)==len(order), "invalid_reasons":invalid, "inventory":inventory, "order":order, "results":results,
            "score":score(results), "started_epoch":started, "finished_epoch":time.time()}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--candidate",required=True); parser.add_argument("--profile",choices=CONFIG["profiles"],required=True)
    parser.add_argument("--mode",choices=CONFIG["execution_modes"],default="natural"); parser.add_argument("--only"); parser.add_argument("--output",required=True); args=parser.parse_args()
    receipt=run(Path(args.candidate),args.profile,args.mode,args.only); output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"valid":receipt["valid"],"score":receipt["score"],"output":str(output)},ensure_ascii=False)); return 0 if receipt["valid"] else 2


if __name__ == "__main__": raise SystemExit(main())
