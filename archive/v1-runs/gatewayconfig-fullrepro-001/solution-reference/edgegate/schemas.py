from __future__ import annotations

from typing import Any

from .models import EdgeGateError, clone, ensure_kind


PLUGIN_NAMES = {"add_header", "block", "rewrite_path", "tag"}


def _as_string_list(value: Any, field: str, *, upper: bool = False) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise EdgeGateError("invalid_resource", f"{field} must be a list of strings")
    result = sorted(set(x.upper() if upper else x for x in value))
    return result


def _plugins(value: Any, *, allow_empty: bool = True) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise EdgeGateError("invalid_resource", "plugins must be an object")
    if not allow_empty and not value:
        raise EdgeGateError("invalid_resource", "plugins must not be empty")
    normalized: dict[str, dict[str, Any]] = {}
    for name, cfg in sorted(value.items()):
        if name not in PLUGIN_NAMES or not isinstance(cfg, dict):
            raise EdgeGateError("invalid_resource", f"invalid plugin {name}")
        if name == "add_header":
            if not isinstance(cfg.get("name"), str) or not isinstance(cfg.get("value"), str):
                raise EdgeGateError("invalid_resource", "add_header requires name and value")
            normalized[name] = {"name": cfg["name"], "value": cfg["value"]}
        elif name == "block":
            status = cfg.get("status")
            if not isinstance(status, int) or status < 100 or status > 599:
                raise EdgeGateError("invalid_resource", "block requires HTTP status")
            normalized[name] = {"status": status, "reason": str(cfg.get("reason", ""))}
        elif name == "rewrite_path":
            if not isinstance(cfg.get("prefix"), str) or not isinstance(cfg.get("replacement"), str):
                raise EdgeGateError("invalid_resource", "rewrite_path requires prefix and replacement")
            normalized[name] = {"prefix": cfg["prefix"], "replacement": cfg["replacement"]}
        elif name == "tag":
            if not isinstance(cfg.get("name"), str) or not isinstance(cfg.get("value"), str):
                raise EdgeGateError("invalid_resource", "tag requires name and value")
            normalized[name] = {"name": cfg["name"], "value": cfg["value"]}
    return normalized


def normalize_resource(kind: str, resource_id: str, body: dict[str, Any]) -> dict[str, Any]:
    ensure_kind(kind)
    if not isinstance(resource_id, str) or not resource_id:
        raise EdgeGateError("invalid_resource", "id must be a non-empty string")
    if not isinstance(body, dict):
        raise EdgeGateError("invalid_resource", "body must be an object")
    raw = clone(body)
    raw["id"] = resource_id
    if kind == "upstream":
        return _upstream(raw)
    if kind == "service":
        return _service(raw)
    if kind == "plugin_config":
        return _plugin_config(raw)
    if kind == "global_rule":
        return _global_rule(raw)
    if kind == "route":
        return _route(raw)
    raise AssertionError(kind)


def _tags(raw: dict[str, Any]) -> list[str]:
    return _as_string_list(raw.get("tags"), "tags")


def _upstream(raw: dict[str, Any]) -> dict[str, Any]:
    nodes = raw.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise EdgeGateError("invalid_resource", "upstream nodes must be non-empty")
    normalized_nodes = []
    seen = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise EdgeGateError("invalid_resource", "node must be an object")
        node_id = node.get("id")
        url = node.get("url")
        weight = node.get("weight", 1)
        if not isinstance(node_id, str) or not node_id or node_id in seen:
            raise EdgeGateError("invalid_resource", "node id must be unique")
        if not isinstance(url, str) or "://" not in url:
            raise EdgeGateError("invalid_resource", "node url must include scheme")
        if not isinstance(weight, int) or weight <= 0:
            raise EdgeGateError("invalid_resource", "node weight must be positive")
        seen.add(node_id)
        normalized_nodes.append({"id": node_id, "url": url, "weight": weight})
    timeout = raw.get("timeout_ms", 5000)
    if not isinstance(timeout, int) or timeout <= 0:
        raise EdgeGateError("invalid_resource", "timeout_ms must be positive")
    return {"id": raw["id"], "nodes": sorted(normalized_nodes, key=lambda x: x["id"]), "timeout_ms": timeout, "tags": _tags(raw)}


def _service(raw: dict[str, Any]) -> dict[str, Any]:
    upstream_id = raw.get("upstream_id")
    if not isinstance(upstream_id, str) or not upstream_id:
        raise EdgeGateError("invalid_resource", "service requires upstream_id")
    return {"id": raw["id"], "upstream_id": upstream_id, "plugins": _plugins(raw.get("plugins")), "tags": _tags(raw)}


def _plugin_config(raw: dict[str, Any]) -> dict[str, Any]:
    return {"id": raw["id"], "plugins": _plugins(raw.get("plugins"), allow_empty=False)}


def _global_rule(raw: dict[str, Any]) -> dict[str, Any]:
    return {"id": raw["id"], "plugins": _plugins(raw.get("plugins"), allow_empty=False)}


def _route(raw: dict[str, Any]) -> dict[str, Any]:
    paths = _as_string_list(raw.get("paths"), "paths")
    if not paths:
        raise EdgeGateError("invalid_resource", "route requires paths")
    service_id = raw.get("service_id")
    upstream_id = raw.get("upstream_id")
    plugin_config_id = raw.get("plugin_config_id")
    if service_id is not None and (not isinstance(service_id, str) or not service_id):
        raise EdgeGateError("invalid_resource", "service_id must be a string")
    if upstream_id is not None and (not isinstance(upstream_id, str) or not upstream_id):
        raise EdgeGateError("invalid_resource", "upstream_id must be a string")
    if plugin_config_id is not None and (not isinstance(plugin_config_id, str) or not plugin_config_id):
        raise EdgeGateError("invalid_resource", "plugin_config_id must be a string")
    if not service_id and not upstream_id:
        raise EdgeGateError("invalid_resource", "route requires service_id or upstream_id")
    priority = raw.get("priority", 0)
    if not isinstance(priority, int):
        raise EdgeGateError("invalid_resource", "priority must be an integer")
    return {
        "id": raw["id"],
        "methods": _as_string_list(raw.get("methods"), "methods", upper=True),
        "hosts": _as_string_list(raw.get("hosts"), "hosts"),
        "paths": paths,
        "priority": priority,
        "service_id": service_id,
        "upstream_id": upstream_id,
        "plugin_config_id": plugin_config_id,
        "plugins": _plugins(raw.get("plugins")),
    }
