#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = json.loads((ROOT / "rubric.json").read_text(encoding="utf-8"))


class CheckFailure(AssertionError):
    pass


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise CheckFailure(msg or f"expected {expected!r}, got {actual!r}")


def assert_true(value, msg=""):
    if not value:
        raise CheckFailure(msg or f"expected truthy value, got {value!r}")


def assert_error(fn: Callable, code: str):
    try:
        fn()
    except Exception as exc:
        if getattr(exc, "code", None) == code:
            return
        raise CheckFailure(f"expected error code {code}, got {getattr(exc, 'code', type(exc).__name__)}") from exc
    raise CheckFailure(f"expected error code {code}, no error raised")


def new_gate(path=None):
    from edgegate import EdgeGate

    return EdgeGate(path)


def base_gate():
    g = new_gate()
    g.put("upstream", "up-a", {"nodes": [{"id": "n1", "url": "http://a", "weight": 2}, {"id": "n2", "url": "http://b", "weight": 1}]})
    g.put("upstream", "up-b", {"nodes": [{"id": "b1", "url": "http://c", "weight": 1}]})
    g.put("service", "svc-a", {"upstream_id": "up-a", "plugins": {"tag": {"name": "svc", "value": "A"}}})
    g.put("plugin_config", "pc-a", {"plugins": {"add_header": {"name": "X-PC", "value": "yes"}}})
    g.put("global_rule", "global-a", {"plugins": {"tag": {"name": "global", "value": "on"}}})
    g.put("route", "r-a", {"methods": ["GET"], "hosts": ["api.example"], "paths": ["/v1/*"], "priority": 10, "service_id": "svc-a", "plugin_config_id": "pc-a", "plugins": {"rewrite_path": {"prefix": "/v1", "replacement": "/api"}}})
    return g


def standalone_doc():
    return {
        "upstreams": [{"id": "up-a", "nodes": [{"id": "n1", "url": "http://a", "weight": 1}]}],
        "services": [{"id": "svc-a", "upstream_id": "up-a"}],
        "plugin_configs": [{"id": "pc-a", "plugins": {"add_header": {"name": "X-PC", "value": "yes"}}}],
        "global_rules": [{"id": "global-a", "plugins": {"tag": {"name": "g", "value": "1"}}}],
        "routes": [{"id": "r-a", "paths": ["/v1/*"], "hosts": ["api.example"], "service_id": "svc-a", "plugin_config_id": "pc-a", "priority": 5}],
    }


def test_u001():
    from edgegate.schemas import normalize_resource

    assert_error(lambda: normalize_resource("upstream", "bad", {"nodes": []}), "invalid_resource")
    assert_error(lambda: normalize_resource("upstream", "bad", {"nodes": [{"id": "n", "url": "http://x", "weight": 0}]}), "invalid_resource")


def test_u002():
    from edgegate.schemas import normalize_resource

    assert_error(lambda: normalize_resource("route", "r", {"paths": []}), "invalid_resource")
    assert_error(lambda: normalize_resource("route", "r", {"paths": ["/"], "methods": ["GET"]}), "invalid_resource")


def test_u003():
    from edgegate.schemas import normalize_resource

    rec = normalize_resource("route", "r", {"paths": ["/b", "/a"], "methods": ["post", "GET"], "upstream_id": "u"})
    assert_eq(rec["methods"], ["GET", "POST"])
    assert_eq(rec["paths"], ["/a", "/b"])


def test_u004():
    from edgegate.models import digest_value
    from edgegate.schemas import normalize_resource

    a = normalize_resource("upstream", "u", {"tags": ["b", "a"], "nodes": [{"url": "http://x", "weight": 1, "id": "n"}]})
    b = normalize_resource("upstream", "u", {"nodes": [{"id": "n", "url": "http://x", "weight": 1}], "tags": ["a", "b"]})
    assert_eq(digest_value(a), digest_value(b))


def test_u005():
    from edgegate.schemas import normalize_resource
    from edgegate.store import ResourceStore

    store = ResourceStore()
    body = normalize_resource("upstream", "u", {"nodes": [{"id": "n", "url": "http://x", "weight": 1}]})
    a = store.put_record("upstream", "u", body)
    b = store.put_record("upstream", "u", body)
    assert_eq(a.version, b.version)
    assert_eq(store.audit[-1]["action"], "noop_put")


def test_u006():
    from edgegate.patches import merge_patch

    before = {"paths": ["/v1/*"], "priority": 10, "plugins": {"tag": {"name": "x", "value": "y"}}}
    after = merge_patch(before, {"priority": 20})
    assert_eq(after["paths"], before["paths"])
    assert_eq(after["priority"], 20)


def test_u007():
    from edgegate.patches import merge_patch

    after = merge_patch({"hosts": ["api.example"], "paths": ["/old"]}, {"hosts": None, "paths": ["/new"]})
    assert_true("hosts" not in after)
    assert_eq(after["paths"], ["/new"])


def test_u008():
    g = base_gate()
    refs = g.reference_report()["forward"]
    assert_true(any(r["from_id"] == "r-a" and r["to_id"] == "svc-a" for r in refs))
    assert_true(any(r["from_id"] == "r-a" and r["to_id"] == "pc-a" for r in refs))


def test_u009():
    g = base_gate()
    assert_true(g.reference_report()["reverse"]["service:svc-a"])
    g.patch("route", "r-a", {"upstream_id": "up-b", "service_id": None})
    assert_true("service:svc-a" not in g.reference_report()["reverse"])


def test_u010():
    g = base_gate()
    rec = g.delete("upstream", "up-a", force=True)
    assert_true(rec["tombstone"])
    assert_true(g.reference_report()["dangling"])


def test_u011():
    g1 = new_gate(); g2 = new_gate()
    a = g1.load_standalone(standalone_doc())["digest"]
    doc = standalone_doc()
    doc["routes"] = list(reversed(doc["routes"]))
    b = g2.load_standalone(doc)["digest"]
    assert_eq(a, b)


def test_u012():
    g = base_gate()
    old = g.config_report()["digest"]
    bad = standalone_doc()
    bad["routes"][0]["service_id"] = "missing"
    assert_error(lambda: g.load_standalone(bad), "standalone_rejected")
    assert_eq(g.config_report()["digest"], old)


def test_u013():
    from edgegate.matcher import match_route

    routes = [{"id": "low", "paths": ["/x"], "priority": 1}, {"id": "high", "paths": ["/x"], "priority": 9}]
    assert_eq(match_route(routes, "GET", "h", "/x")["id"], "high")


def test_u014():
    from edgegate.matcher import match_route

    routes = [{"id": "a", "paths": ["/x/*"], "priority": 1}, {"id": "b", "paths": ["/x/y"], "priority": 1}]
    assert_eq(match_route(routes, "GET", "h", "/x/y")["id"], "b")


def test_u015():
    g = base_gate()
    g.patch("route", "r-a", {"upstream_id": "up-b"})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["upstream_id"], "up-b")


def test_u016():
    from edgegate.balancer import select_node

    upstream = {"id": "up-a", "nodes": [{"id": "n1", "url": "http://a", "weight": 2}, {"id": "n2", "url": "http://b", "weight": 1}]}
    counters = {}
    ids = [select_node(upstream, counters)["id"] for _ in range(4)]
    assert_eq(ids, ["n1", "n1", "n2", "n1"])


def test_u017():
    from edgegate.plugins import merge_plugins

    plan = merge_plugins(
        [{"id": "global-a", "plugins": {"tag": {"name": "global", "value": "on"}}}],
        {"id": "svc-a", "plugins": {"tag": {"name": "svc", "value": "A"}}},
        None,
        {"id": "r-a", "plugins": {"tag": {"name": "route", "value": "R"}}},
    )
    assert_eq(plan["final"]["tag"]["source"], "route:r-a")
    assert_true(plan["overrides"])


def test_u018():
    from edgegate.plugins import apply_plugins, merge_plugins

    plan = merge_plugins([{"id": "block-all", "plugins": {"block": {"status": 451, "reason": "policy"}}}], None, None, None)
    res = apply_plugins(plan, {"path": "/v1/a", "headers": {}}, upstream_selected=True)
    assert_eq(res["status"], 451)
    assert_true(res["blocked"])


def test_u019():
    g = base_gate()
    g.delete("route", "r-a")
    assert_true(all(e.get("id") != "r-a" for e in g.audit_report()))
    assert_true(any(e.get("id") == "r-a" for e in g.audit_report(include_deleted=True)))


def test_u020():
    g = base_gate()
    report = g.runtime_report()
    sim = g.simulate_request("GET", "api.example", "/v1/a")
    assert_eq(report["routes"][0]["route_id"], sim["route_id"])


def test_i001():
    g = base_gate()
    assert_eq(len(g.list("upstream")), 2)
    assert_eq(g.get("service", "svc-a")["body"]["upstream_id"], "up-a")


def test_i002():
    g = base_gate()
    report = g.config_report()
    assert_eq(report["resources"]["route"]["versions"]["r-a"], 1)
    assert_true(report["digest"])


def test_i003():
    g = base_gate()
    g.patch("route", "r-a", {"paths": ["/v2/*"]})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["status"], 404)
    assert_eq(g.simulate_request("GET", "api.example", "/v2/a")["route_id"], "r-a")


def test_i004():
    g = base_gate()
    assert_error(lambda: g.delete("upstream", "up-a"), "reference_conflict")


def test_i005():
    g = base_gate()
    g.delete("upstream", "up-a", force=True)
    assert_true(g.reference_report()["dangling"])
    assert_eq(g.audit_report(include_deleted=True)[-1]["action"], "force_delete")


def test_i006():
    g = new_gate()
    res = g.load_standalone(standalone_doc())
    assert_eq(g.get("route", "r-a")["body"]["service_id"], "svc-a")
    assert_true(res["changed"])


def test_i007():
    g = new_gate()
    first = g.load_standalone(standalone_doc())
    second = g.load_standalone(standalone_doc())
    assert_eq(first["generation"], second["generation"])
    assert_true(not second["changed"])


def test_i008():
    g = base_gate()
    assert_eq(g.simulate_request("GET", "api.example", "/v1/users")["route_id"], "r-a")


def test_i009():
    g = base_gate()
    res = g.simulate_request("GET", "api.example", "/v1/users")
    assert_eq(res["upstream_version"], 1)
    assert_true(res["selected_node"])


def test_i010():
    g = base_gate()
    res = g.simulate_request("GET", "api.example", "/v1/users")
    assert_true("add_header" in res["plugin_plan"]["final"])


def test_i011():
    g = base_gate()
    assert_eq(g.simulate_request("GET", "api.example", "/v1/users")["rewritten_path"], "/api/users")


def test_i012():
    g = base_gate()
    assert_eq(g.simulate_request("GET", "api.example", "/v1/users")["headers"]["X-PC"], "yes")


def test_i013():
    g = base_gate()
    assert_eq(g.config_report()["digest"], g.store.config_digest)


def test_i014():
    g = base_gate()
    assert_eq(g.runtime_report()["routes"][0]["route_id"], g.simulate_request("GET", "api.example", "/v1/users")["route_id"])


def _run_cli(solution_dir: Path, args: list[str], env_extra=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(solution_dir)
    proc = subprocess.run([sys.executable, "-m", "edgegate.cli", *args], capture_output=True, text=True, env=env, check=False)
    if proc.returncode not in (0, 2):
        raise CheckFailure(proc.stderr or proc.stdout)
    return proc.returncode, json.loads(proc.stdout)


def test_i015(solution_dir=None):
    with tempfile.TemporaryDirectory() as td:
        state = Path(td) / "state.json"
        doc = Path(td) / "doc.json"
        doc.write_text(json.dumps(standalone_doc()), encoding="utf-8")
        code, applied = _run_cli(solution_dir, ["--state", str(state), "apply", str(doc)])
        assert_eq(code, 0)
        code, report = _run_cli(solution_dir, ["--state", str(state), "report", "config"])
        assert_eq(report["digest"], applied["digest"])


def test_i016(solution_dir=None):
    with tempfile.TemporaryDirectory() as td:
        state = Path(td) / "state.json"
        doc = Path(td) / "doc.json"
        doc.write_text(json.dumps(standalone_doc()), encoding="utf-8")
        _run_cli(solution_dir, ["--state", str(state), "apply", str(doc)])
        _, res = _run_cli(solution_dir, ["--state", str(state), "simulate", "GET", "api.example", "/v1/x"])
        assert_eq(res["route_id"], "r-a")


def test_i017():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "state.json"
        g = base_gate()
        g.store.path = path
        g.store.save()
        g2 = new_gate(path)
        assert_eq(g2.get("route", "r-a")["version"], 1)
        assert_eq(g2.config_report()["digest"], g.config_report()["digest"])


def test_i018():
    g = base_gate()
    old = g.simulate_request("GET", "api.example", "/v1/a")
    bad = standalone_doc(); bad["routes"][0]["upstream_id"] = "missing"; bad["routes"][0].pop("service_id", None)
    assert_error(lambda: g.load_standalone(bad), "standalone_rejected")
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["route_id"], old["route_id"])


def test_i019():
    g = base_gate()
    g.patch("route", "r-a", {"upstream_id": "up-b", "service_id": None})
    assert_true("upstream:up-b" in g.reference_report()["reverse"])


def test_i020():
    g = base_gate()
    g.patch("route", "r-a", {"plugin_config_id": None})
    assert_true("add_header" not in g.simulate_request("GET", "api.example", "/v1/a")["plugin_plan"]["final"])


def test_s001():
    test_i001(); test_i002(); test_i008()


def test_s002():
    g = base_gate()
    g.put("route", "r-b", {"paths": ["/v1/*"], "hosts": ["api.example"], "priority": 30, "upstream_id": "up-b"})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["route_id"], "r-b")
    g.patch("route", "r-a", {"priority": 40})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["route_id"], "r-a")


def test_s003():
    g = base_gate()
    g.patch("service", "svc-a", {"upstream_id": "up-b"})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["upstream_id"], "up-b")
    assert_true("upstream:up-b" in g.reference_report()["reverse"])


def test_s004():
    test_u017()


def test_s005():
    test_u018()


def test_s006():
    g = base_gate()
    g.delete("upstream", "up-a", force=True)
    sim = g.simulate_request("GET", "api.example", "/v1/a")
    assert_eq(sim["error"], "missing_upstream")
    assert_true(g.reference_report()["dangling"])


def test_s007():
    g = base_gate()
    doc = standalone_doc()
    doc["routes"] = []
    res = g.load_standalone(doc)
    assert_true(res["changed"])
    assert_error(lambda: g.get("route", "r-a"), "not_found")
    assert_true(any(e["action"] == "standalone_reload" for e in g.audit_report(include_deleted=True)))


def test_s008():
    test_i007()


def test_s009():
    g = base_gate()
    g.delete("route", "r-a")
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["status"], 404)
    assert_true(any(e.get("id") == "r-a" for e in g.audit_report(include_deleted=True)))


def test_s010():
    test_i017()


def test_s011(solution_dir=None):
    test_i015(solution_dir)
    test_i016(solution_dir)


def test_s012():
    test_u014()


def test_s013():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "state.json"
        g = base_gate()
        g.store.path = path
        first = g.simulate_request("GET", "api.example", "/v1/a")["selected_node"]["id"]
        g.config_report()
        g.store.save()
        g2 = new_gate(path)
        second = g2.simulate_request("GET", "api.example", "/v1/a")["selected_node"]["id"]
        assert_eq((first, second), ("n1", "n1"))


def test_s014():
    g = base_gate()
    before = g.config_report()
    assert_error(lambda: g.patch("route", "r-a", {"id": "x"}), "invalid_patch")
    assert_eq(g.config_report(), before)


def test_s015():
    g = base_gate()
    g.patch("route", "r-a", {"plugins": {"tag": {"name": "route", "value": "R"}}})
    sim = g.simulate_request("GET", "api.example", "/v1/a")
    assert_eq(sim["tags"]["route"], "R")
    assert_eq(sim["plugin_plan"]["final"]["tag"]["source"], "route:r-a")


def test_s016():
    g = base_gate()
    route_ver = g.get("route", "r-a")["version"]
    g.patch("plugin_config", "pc-a", {"plugins": {"add_header": {"name": "X-PC", "value": "changed"}}})
    assert_eq(g.get("route", "r-a")["version"], route_ver)
    assert_eq(g.simulate_request("GET", "api.example", "/v1/a")["headers"]["X-PC"], "changed")


def test_s017():
    g = base_gate()
    before = len(g.runtime_report()["routes"])
    g.delete("global_rule", "global-a")
    after = g.runtime_report()
    assert_eq(len(after["routes"]), before)
    assert_true("global_rule:global-a" not in str(after))


def test_s018():
    g = base_gate()
    g.put("route", "r-b", {"paths": ["/v1/admin"], "hosts": ["api.example"], "service_id": "svc-a", "priority": 10})
    assert_eq(g.simulate_request("GET", "api.example", "/v1/admin")["route_id"], "r-b")
    assert_eq(g.simulate_request("GET", "api.example", "/v1/other")["route_id"], "r-a")


def test_s019():
    g = base_gate()
    g.delete("upstream", "up-a", force=True)
    before = g.reference_report()["dangling"]
    bad = standalone_doc(); bad["routes"][0]["service_id"] = "missing"
    assert_error(lambda: g.load_standalone(bad), "standalone_rejected")
    assert_eq(g.reference_report()["dangling"], before)


def test_s020(solution_dir=None):
    test_s002()
    test_s003()
    test_s006()
    test_s011(solution_dir)


CHECKS = {name.upper().replace("TEST_", "EG-").replace("_", "-"): obj for name, obj in list(globals().items()) if name.startswith("test_")}


def run_check(check, solution_dir: Path):
    fn = CHECKS[check["id"]]
    try:
        if "solution_dir" in fn.__code__.co_varnames:
            fn(solution_dir=solution_dir)
        else:
            fn()
        return {"id": check["id"], "layer": check["layer"], "name": check["contract"], "passed": True}
    except Exception as exc:
        return {"id": check["id"], "layer": check["layer"], "name": check["contract"], "passed": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution-dir", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    solution_dir = args.solution_dir.resolve()
    sys.path.insert(0, str(solution_dir))
    importlib.invalidate_caches()
    results = [run_check(check, solution_dir) for check in RUBRIC["checks"]]
    passed = sum(1 for result in results if result["passed"])
    by_layer = {}
    for result in results:
        layer = result["layer"]
        by_layer.setdefault(layer, {"passed": 0, "total": 0})
        by_layer[layer]["total"] += 1
        if result["passed"]:
            by_layer[layer]["passed"] += 1
    report = {
        "task": RUBRIC["task_id"],
        "solution_dir": str(solution_dir),
        "passed": passed,
        "total": len(results),
        "score": round(passed * 100 / len(results), 2),
        "by_layer": by_layer,
        "results": results,
    }
    rendered = json.dumps(report, indent=2, sort_keys=False)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
