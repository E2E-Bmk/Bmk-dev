from __future__ import annotations
import contextlib, importlib, inspect, io, json, os, sys, tempfile, time, traceback, warnings
from pathlib import Path
GATE=Path(__file__).resolve().parent
def inside(path: Path, root: Path)->bool:
    try: path.resolve().relative_to(root.resolve()); return True
    except ValueError: return False
def root_module(root: str)->str:
    if root in {*(f"A{i:02d}" for i in range(1,9)),*(f"I{i:02d}" for i in range(1,5)),"S01","S02"}: return "tests.test_native_controls"
    if root.startswith("A"): return "tests.test_recovery_atomic"
    if root.startswith("I"): return "tests.test_recovery_integration"
    return "tests.test_recovery_system"
def semantic_exception_is_valid(phase: str, exc: BaseException)->bool: return phase=="call" and not isinstance(exc,Warning)
def main()->int:
    if len(sys.argv)!=4: print(json.dumps({"valid":False,"error":"usage"})); return 2
    root,candidate_arg,profile=sys.argv[1:]; candidate=Path(candidate_arg).resolve(); payload={"root":root,"valid":True,"passed":False,"phase":"setup","profile":profile}
    stdout,stderr=io.StringIO(),io.StringIO(); started=time.perf_counter()
    if not (candidate/"quart_workflow"/"__init__.py").is_file(): print(json.dumps({**payload,"valid":False,"error":"candidate quart_workflow package is absent"})); return 0
    sys.path.insert(0,str(candidate)); sys.path.insert(1,str(GATE)); os.environ["SPEC2REPO_CANDIDATE_ROOT"]=str(candidate)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error"); importlib.import_module("quart_workflow"); importlib.import_module("quart")
            for loaded in [n for n in sys.modules if n=="tests" or n.startswith("tests.")]: del sys.modules[loaded]
            module=importlib.import_module(root_module(root)); function=getattr(module,f"test_{root.lower()}")
            if [p.name for p in inspect.signature(function).parameters.values()]!=["tmp_path"]: raise TypeError("root signature")
            payload["phase"]="call"; parent=GATE/".tmp"/"roots"; parent.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=root.lower()+"-",dir=parent) as directory:
                with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr): function(Path(directory))
        payload["passed"]=True
    except AssertionError as exc:
        payload.update(exception_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
        if payload["phase"]!="call": payload.update(valid=False,infrastructure_error="assertion before semantic call")
    except BaseException as exc:
        payload.update(exception_type=type(exc).__name__,failure=str(exc),traceback=traceback.format_exc())
        if not semantic_exception_is_valid(str(payload["phase"]),exc): payload.update(valid=False,infrastructure_error="setup or warning failure")
    escaped=[]; allowed_runtime=Path(os.environ["SPEC2REPO_QUART_RUNTIME"]).resolve()
    for name,module in list(sys.modules.items()):
        location=getattr(module,"__file__",None)
        if name=="quart_workflow" or name.startswith("quart_workflow."):
            if location and not inside(Path(location),candidate): escaped.append({"module":name,"path":str(Path(location).resolve())})
        elif name=="quart" or name.startswith("quart."):
            allowed = inside(Path(location),allowed_runtime) if location else False
            if profile=="dummy" and location: allowed = allowed or inside(Path(location),candidate)
            if location and not allowed: escaped.append({"module":name,"path":str(Path(location).resolve())})
    origin=getattr(sys.modules.get("quart_workflow"),"__file__",None); payload["candidate_contained"]=bool(origin and inside(Path(origin),candidate)); payload["escaped_modules"]=escaped
    if not payload["candidate_contained"] or escaped: payload.update(valid=False,infrastructure_error="module provenance escaped declared roots")
    payload.update(stdout=stdout.getvalue(),stderr=stderr.getvalue(),duration_seconds=round(time.perf_counter()-started,6)); print(json.dumps(payload,ensure_ascii=False,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
