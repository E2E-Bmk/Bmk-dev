from __future__ import annotations

import argparse, ast, hashlib, json, os, random, subprocess, sys, time, warnings
from pathlib import Path

GATE=Path(__file__).resolve().parent;CONFIG=json.loads((GATE/"SCORER-CONFIG.json").read_text(encoding="utf-8"));ROOT_MAP=json.loads((GATE/"ROOT-MAP.json").read_text(encoding="utf-8"))
GATE_INPUTS=("TASK.md","SPEC.md","ENVIRONMENT-CONTRACT.md","ANCHOR-ADMISSION-PREREG.md","ROOT-MAP.json","MUTATION-PORTFOLIO.json","SCORER-CONFIG.json","RUNTIME-IDENTITY.json","run_root.py","score_gate.py","probe_source_blank.py","finalize_gate.py","reference-overlay/boltons_v3_cachefabric.py","reference-overlay/boltons_v3_controls.py","clean-api-scaffold/boltons_v3_scaffold.py","tests/support.py","tests/test_native.py","tests/test_atomic.py","tests/test_integration.py","tests/test_system.py","dummy/boltons/__init__.py","dummy/boltons/cachefabric.py","shallow-source-blank/boltons/__init__.py","shallow-source-blank/boltons/cachefabric.py")


def tree_hash(root):
    root=Path(root);digest=hashlib.sha256();ignored={".git","__pycache__",".tmp",".pytest_cache"}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not ignored.intersection(p.relative_to(root).parts) and p.suffix not in {".pyc",".pyo"}):
        rel=path.relative_to(root).as_posix().encode();data=path.read_bytes();digest.update(len(rel).to_bytes(8,"big"));digest.update(rel);digest.update(len(data).to_bytes(8,"big"));digest.update(data)
    return digest.hexdigest()


def gate_hash():
    digest=hashlib.sha256()
    for name in GATE_INPUTS:
        data=(GATE/name).read_bytes();encoded=name.encode();digest.update(len(encoded).to_bytes(8,"big"));digest.update(encoded);digest.update(len(data).to_bytes(8,"big"));digest.update(data)
    return digest.hexdigest()


def runtime_probe():
    identity=json.loads((GATE/CONFIG["declared_runtime_identity"]).read_text(encoding="utf-8"));root=GATE/CONFIG["declared_runtime_site"];files=[p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc",".pyo"}];errors=[]
    if tree_hash(root)!=identity["runtime_tree_sha256"]:errors.append("runtime tree hash")
    if len(files)!=identity["file_count"]:errors.append("runtime file count")
    cache=root/"boltons"/"cacheutils.py"
    if hashlib.sha256(cache.read_bytes()).hexdigest()!=identity["cacheutils_sha256"]:errors.append("cacheutils hash")
    return {"valid":not errors,"errors":errors,"tree_sha256":tree_hash(root),"file_count":len(files),"python":sys.version.split()[0],"identity":identity}


def git_state():
    repo=Path(CONFIG["reference_repository_root"]);cmd=[CONFIG["git_executable"],"-c",f"safe.directory={repo}","-C",str(repo)]
    def run(*args):return subprocess.run([*cmd,*args],text=True,encoding="utf-8",errors="replace",capture_output=True).stdout.strip()
    return {"commit":run("rev-parse","HEAD"),"tree":run("rev-parse","HEAD^{tree}"),"status":run("status","--porcelain=v1","--untracked-files=all")}


def inventory():
    errors=[];ids=[];expected={r["id"] for r in ROOT_MAP["roots"]}
    for file in ("test_native.py","test_atomic.py","test_integration.py","test_system.py"):
        tree=ast.parse((GATE/"tests"/file).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test_"):ids.append(node.name[5:].upper())
    if len(ids)!=48 or set(ids)!=expected or len(ids)!=len(set(ids)):errors.append("root inventory mismatch")
    if sum(r["tier"]=="atomic" for r in ROOT_MAP["roots"])!=16 or sum(r["tier"]=="integration" for r in ROOT_MAP["roots"])!=24 or sum(r["tier"]=="system" for r in ROOT_MAP["roots"])!=8:errors.append("tier counts")
    if sum(r["class"]=="native" for r in ROOT_MAP["roots"])!=14:errors.append("native count")
    return ids,errors


def ordered(mode):
    ids=[r["id"] for r in ROOT_MAP["roots"]]
    if mode=="reverse":return list(reversed(ids))
    if mode=="permuted":random.Random(CONFIG["permutation_seed"]).shuffle(ids)
    return ids


def score(results):
    lookup={r["id"]:r for r in ROOT_MAP["roots"]}
    def metric(items):
        total=len(items);passed=sum(bool(r["passed"]) for r in items);return {"passed":passed,"total":total,"rate":round(passed/total,8) if total else None}
    atomic=[r for r in results if lookup[r["root"]]["tier"]=="atomic"];composition=[r for r in results if lookup[r["root"]]["tier"]!="atomic"];native=[r for r in results if lookup[r["root"]]["class"]=="native"];mutation=[r for r in results if lookup[r["root"]]["class"]=="mutation"]
    families={}
    for row in ROOT_MAP["roots"]:
        if row["class"]=="mutation":families.setdefault(row["family"],[])
    for result in mutation:families[lookup[result["root"]]["family"]].append(result)
    a=metric(atomic);c=metric(composition)
    gap=round(a["rate"]-c["rate"],8) if a["rate"] is not None and c["rate"] is not None else None
    return {"all_roots":metric(results),"atomic":a,"composition":c,"integration":metric([r for r in results if lookup[r["root"]]["tier"]=="integration"]),"system_e2e":metric([r for r in results if lookup[r["root"]]["tier"]=="system"]),"gap":gap,"native_controls":metric(native),"mutation_designated":metric(mutation),"mutation_families":{name:metric(items) for name,items in sorted(families.items())}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--candidate",required=True);parser.add_argument("--profile",choices=CONFIG["profiles"],required=True);parser.add_argument("--mode",choices=CONFIG["execution_modes"],default="natural");parser.add_argument("--only");parser.add_argument("--output",required=True);args=parser.parse_args()
    candidate=Path(args.candidate).resolve();before=tree_hash(candidate);reference_before=git_state();runtime=runtime_probe();ids,inv_errors=inventory();run_ids=[args.only] if args.only else ordered(args.mode);results=[];invalid=list(inv_errors)
    if args.only not in {None,*ids}:invalid.append("unknown root")
    started=time.time()
    for root in run_ids:
        try:child=subprocess.run([sys.executable,"-X","utf8","-B",str(GATE/"run_root.py"),root,str(candidate),args.profile],text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=CONFIG["root_timeout_seconds"])
        except subprocess.TimeoutExpired:results.append({"root":root,"valid":False,"passed":False,"infrastructure_error":"timeout"});invalid.append(root+": timeout");continue
        try:record=json.loads(child.stdout)
        except Exception:record={"root":root,"valid":False,"passed":False,"infrastructure_error":"malformed child receipt","stdout":child.stdout,"stderr":child.stderr}
        if child.returncode!=0:record.update(valid=False,infrastructure_error="child nonzero")
        if record.get("valid") is not True:invalid.append(root+": "+str(record.get("infrastructure_error","invalid")))
        results.append(record)
    after=tree_hash(candidate);reference_after=git_state()
    if before!=after:invalid.append("candidate tree changed")
    if reference_before!=reference_after or reference_after!={"commit":CONFIG["reference_commit"],"tree":CONFIG["reference_tree"],"status":""}:invalid.append("reference provenance")
    if runtime["valid"] is not True:invalid.append("runtime identity")
    receipt={"schema":"spec2repo.score-receipt.v3","case":CONFIG["case"],"constitution":CONFIG["constitution"],"valid":not invalid,"invalid_reasons":invalid,"profile":args.profile,"mode":args.mode,"only":args.only,"candidate":str(candidate),"candidate_tree_sha256_before":before,"candidate_tree_sha256_after":after,"reference_before":reference_before,"reference_after":reference_after,"runtime_identity":runtime,"gate_input_sha256":gate_hash(),"results":results,"score":score(results),"started_epoch":started,"finished_epoch":time.time()}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps({"valid":receipt["valid"],"score":receipt["score"],"output":str(output)},ensure_ascii=False));return 0 if receipt["valid"] else 2


if __name__=="__main__":raise SystemExit(main())
