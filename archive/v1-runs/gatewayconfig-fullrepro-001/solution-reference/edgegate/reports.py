from __future__ import annotations

from typing import Any

from .matcher import match_route
from .plugins import merge_plugins
from .references import reference_report


def config_report(gateway) -> dict[str, Any]:
    resources = {}
    for kind in gateway.store.records:
        live = gateway.store.live(kind)
        tombstoned = [rec for rec in gateway.store.records[kind].values() if rec.tombstone]
        resources[kind] = {
            "live": len(live),
            "tombstoned": len(tombstoned),
            "versions": {rec.id: rec.version for rec in sorted(gateway.store.records[kind].values(), key=lambda r: r.id)},
            "digests": {rec.id: rec.digest for rec in sorted(gateway.store.records[kind].values(), key=lambda r: r.id)},
        }
    return {"generation": gateway.store.generation, "digest": gateway.store.config_digest, "resources": resources}


def runtime_report(gateway) -> dict[str, Any]:
    routes = [rec.body for rec in gateway.store.live("route")]
    globals_ = [rec.body for rec in gateway.store.live("global_rule")]
    rows = []
    for route in sorted(routes, key=lambda r: r["id"]):
        service = None
        if route.get("service_id"):
            try:
                service = gateway.store.live_body("service", route["service_id"])
            except Exception:
                service = None
        plugin_config = None
        if route.get("plugin_config_id"):
            try:
                plugin_config = gateway.store.live_body("plugin_config", route["plugin_config_id"])
            except Exception:
                plugin_config = None
        rows.append({
            "route_id": route["id"],
            "priority": route.get("priority", 0),
            "paths": route["paths"],
            "service_id": route.get("service_id"),
            "upstream_id": route.get("upstream_id") or (service or {}).get("upstream_id"),
            "plugin_final": merge_plugins(globals_, service, plugin_config, route)["final"],
        })
    return {
        "generation": gateway.store.generation,
        "digest": gateway.store.config_digest,
        "routes": rows,
        "dangling": reference_report(gateway.store)["dangling"],
        "match_probe": _probe(gateway, routes),
    }


def _probe(gateway, routes):
    samples = []
    for route in routes:
        path = route["paths"][0].replace("*", "probe")
        host = route.get("hosts", ["example.local"])[0].replace("*.", "api.")
        method = route.get("methods", ["GET"])[0]
        matched = match_route(routes, method, host, path)
        samples.append({"route_id": route["id"], "sample": {"method": method, "host": host, "path": path}, "matched_route_id": matched["id"] if matched else None})
    return samples


def audit_report(gateway, include_deleted: bool = False) -> list[dict[str, Any]]:
    if include_deleted:
        return list(gateway.store.audit)
    deleted_ids = {
        (rec.kind, rec.id)
        for rows in gateway.store.records.values()
        for rec in rows.values()
        if rec.tombstone
    }
    return [entry for entry in gateway.store.audit if (entry.get("kind"), entry.get("id")) not in deleted_ids]
