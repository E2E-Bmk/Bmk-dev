from __future__ import annotations

from .models import clone


def _add_source(plan, source, plugins):
    for name, cfg in plugins.items():
        old = plan["final"].get(name)
        if old:
            plan["overrides"].append({"plugin": name, "from": old["source"], "to": source})
        plan["final"][name] = {"source": source, "config": clone(cfg)}
        plan["ordered"].append({"plugin": name, "source": source, "config": clone(cfg)})


def merge_plugins(global_rules, service, plugin_config, route) -> dict:
    plan = {"ordered": [], "overrides": [], "final": {}}
    for rule in sorted(global_rules, key=lambda x: x["id"]):
        _add_source(plan, f"global_rule:{rule['id']}", rule.get("plugins", {}))
    if service:
        _add_source(plan, f"service:{service['id']}", service.get("plugins", {}))
    if plugin_config:
        _add_source(plan, f"plugin_config:{plugin_config['id']}", plugin_config.get("plugins", {}))
    if route:
        _add_source(plan, f"route:{route['id']}", route.get("plugins", {}))
    return plan


def apply_plugins(plan: dict, request: dict, upstream_selected: bool = True) -> dict:
    path = request["path"]
    headers = dict(request.get("headers") or {})
    tags = {}
    status = 200 if upstream_selected else 503
    blocked = False
    final = {name: entry["config"] for name, entry in plan["final"].items()}
    if "rewrite_path" in final:
        cfg = final["rewrite_path"]
        if path.startswith(cfg["prefix"]):
            path = cfg["replacement"] + path[len(cfg["prefix"]):]
    if "add_header" in final:
        cfg = final["add_header"]
        headers[cfg["name"]] = cfg["value"]
    if "tag" in final:
        cfg = final["tag"]
        tags[cfg["name"]] = cfg["value"]
    if "block" in final:
        cfg = final["block"]
        status = cfg["status"]
        blocked = True
    return {"path": path, "headers": headers, "tags": tags, "status": status, "blocked": blocked}
