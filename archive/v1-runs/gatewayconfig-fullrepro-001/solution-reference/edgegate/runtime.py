from __future__ import annotations

from typing import Any

from .balancer import select_node
from .matcher import match_route
from .models import EdgeGateError, clone
from .plugins import apply_plugins, merge_plugins


def _version(gateway, kind: str, rid: str | None) -> int | None:
    if not rid:
        return None
    try:
        return gateway.store.get_record(kind, rid).version
    except EdgeGateError:
        return None


def simulate_request(gateway, method: str, host: str, path: str, headers=None) -> dict[str, Any]:
    routes = [rec.body for rec in gateway.store.live("route")]
    route = match_route(routes, method, host, path)
    base = {
        "method": method.upper(),
        "host": host,
        "path": path,
        "generation": gateway.store.generation,
        "config_digest": gateway.store.config_digest,
    }
    if route is None:
        return {**base, "matched": False, "status": 404, "route_id": None, "error": "no_route"}

    service = None
    if route.get("service_id"):
        try:
            service = gateway.store.live_body("service", route["service_id"])
        except EdgeGateError:
            return {**base, "matched": True, "route_id": route["id"], "status": 503, "error": "missing_service"}

    upstream_id = route.get("upstream_id") or (service or {}).get("upstream_id")
    upstream = None
    if upstream_id:
        try:
            upstream = gateway.store.live_body("upstream", upstream_id)
        except EdgeGateError:
            upstream = None

    plugin_config = None
    if route.get("plugin_config_id"):
        try:
            plugin_config = gateway.store.live_body("plugin_config", route["plugin_config_id"])
        except EdgeGateError:
            plugin_config = None

    globals_ = [rec.body for rec in gateway.store.live("global_rule")]
    plan = merge_plugins(globals_, service, plugin_config, route)
    transformed = apply_plugins(plan, {"path": path, "headers": headers or {}}, upstream_selected=upstream is not None)
    selected = None
    if upstream is not None and not transformed["blocked"]:
        selected = select_node(upstream, gateway.store.counters)
        gateway.store.save()

    return {
        **base,
        "matched": True,
        "route_id": route["id"],
        "route_version": _version(gateway, "route", route["id"]),
        "service_id": route.get("service_id"),
        "service_version": _version(gateway, "service", route.get("service_id")),
        "upstream_id": upstream_id,
        "upstream_version": _version(gateway, "upstream", upstream_id),
        "plugin_config_id": route.get("plugin_config_id"),
        "plugin_config_version": _version(gateway, "plugin_config", route.get("plugin_config_id")),
        "selected_node": clone(selected),
        "plugin_plan": plan,
        "rewritten_path": transformed["path"],
        "headers": transformed["headers"],
        "tags": transformed["tags"],
        "status": transformed["status"],
        "blocked": transformed["blocked"],
        "error": None if upstream is not None or transformed["blocked"] else "missing_upstream",
    }
