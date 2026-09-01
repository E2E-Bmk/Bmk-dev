from __future__ import annotations

import contextlib, importlib, inspect, io, json, os, sys, tempfile, time, traceback, warnings
from pathlib import Path

GATE=Path(__file__).resolve().parent


def inside(path,root):
    try:Path(path).resolve().relative_to(Path(root).resolve());return True
    except ValueError:return False


def root_module(root):
    native={*(f"A{i:02d}" for i in range(1,9)),*(f"I{i:02d}" for i in range(1,5)),"S01","S02"}
    if root in native:return "tests.test_native"
    if root.startswith("A"):return "tests.test_atomic"
    if root.startswith("I"):return "tests.test_integration"
    return "tests.test_system"


def install(profile,boltons):
    if profile=="reference":
        sys.path.insert(0,str(GATE/"reference-overlay"));importlib.import_module("boltons_v3_cachefabric").install(boltons)
    elif profile=="clean":
        sys.path.insert(0,str(GATE/"clean-api-scaffold"));importlib.import_module("boltons_v3_scaffold").install(boltons)
    elif profile in {"broad-route","broad-delivery"}:
        sys.path.insert(0,str(GATE/"reference-overlay"));importlib.import_module("boltons_v3_controls").install(boltons,profile)
    elif profile in {"dummy","shallow","anchor","arbitrary"}:return
    else:raise RuntimeError("unknown profile")


def main():
    if len(sys.argv)!=4:print(json.dumps({"valid":False,"error":"usage"}));return 2
    root,candidate_arg,profile=sys.argv[1:];candidate=Path(candidate_arg).resolve();payload={"root":root,"profile":profile,"valid":True,"passed":False,"phase":"setup"};out=io.StringIO();err=io.StringIO();started=time.perf_counter()
    if not (candidate/"boltons"/"__init__.py").is_file():print(json.dumps({**payload,"valid":False,"error":"candidate boltons package absent"}));return 0
    os.environ["SPEC2REPO_BOLTONS_RUNTIME"]=str((GATE/"runtime-site").resolve());sys.path.insert(0,str(candidate));sys.path.insert(1,str(GATE))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error");boltons=importlib.import_module("boltons");install(profile,boltons)
            sys.path.insert(0,str(GATE))
            for name in [n for n in sys.modules if n=="tests" or n.startswith("tests.")]:del sys.modules[name]
            module=importlib.import_module(root_module(root));function=getattr(module,f"test_{root.lower()}")
            if list(inspect.signature(function).parameters)!=["tmp_path"]:raise TypeError("invalid root signature")
            payload["phase"]="call";parent=GATE/".tmp"/"roots";parent.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=root.lower()+"-",dir=parent) as directory:
                with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):function(Path(directory))
        payload["passed"]=True
    except AssertionError as exc:payload.update(exception_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
        if payload["phase"]!="call" or isinstance(exc,Warning):payload.update(valid=False,infrastructure_error="failure before semantic call")
    top=sys.modules.get("boltons");origin=getattr(top,"__file__",None);payload["boltons_import"]=str(Path(origin).resolve()) if origin else None;payload["candidate_contained"]=bool(origin and inside(origin,candidate))
    runtime=(GATE/"runtime-site").resolve();overlay=profile in {"reference","clean","broad-route","broad-delivery"};escaped=[]
    for name,module in list(sys.modules.items()):
        if name!="boltons" and not name.startswith("boltons."):continue
        location=getattr(module,"__file__",None)
        if location and not inside(location,candidate):
            if overlay and name=="boltons.cachefabric":continue
            if inside(location,runtime) and name!="boltons.cachefabric":continue
            escaped.append({"module":name,"path":str(Path(location).resolve())})
    fabric=sys.modules.get("boltons.cachefabric");fabric_origin=getattr(fabric,"__file__",None);payload["cachefabric_import"]=str(Path(fabric_origin).resolve()) if fabric_origin else "overlay";payload["escaped_boltons_modules"]=escaped
    if not payload["candidate_contained"] or escaped:payload.update(valid=False,infrastructure_error="import escaped candidate/runtime roots")
    payload.update(stdout=out.getvalue(),stderr=err.getvalue(),duration_seconds=round(time.perf_counter()-started,6));print(json.dumps(payload,ensure_ascii=False,sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())

