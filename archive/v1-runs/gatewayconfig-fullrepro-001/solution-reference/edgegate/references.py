from __future__ import annotations

from .models import KINDS, EdgeGateError


def direct_refs(kind: str, body: dict) -> list[dict]:
    refs = []
    if kind == "service":
        refs.append({"from_kind": kind, "from_id": body["id"], "to_kind": "upstream", "to_id": body["upstream_id"], "field": "upstream_id"})
    if kind == "route":
        for field, to_kind in (("service_id", "service"), ("upstream_id", "upstream"), ("plugin_config_id", "plugin_config")):
            if body.get(field):
                refs.append({"from_kind": kind, "from_id": body["id"], "to_kind": to_kind, "to_id": body[field], "field": field})
    return refs


def all_forward_refs(store) -> list[dict]:
    refs = []
    for kind in KINDS:
        for rec in store.live(kind):
            refs.extend(direct_refs(kind, rec.body))
    return sorted(refs, key=lambda r: (r["from_kind"], r["from_id"], r["field"]))


def reverse_refs(store, to_kind: str, to_id: str) -> list[dict]:
    return [ref for ref in all_forward_refs(store) if ref["to_kind"] == to_kind and ref["to_id"] == to_id]


def missing_refs(store) -> list[dict]:
    missing = []
    for ref in all_forward_refs(store):
        try:
            store.live_body(ref["to_kind"], ref["to_id"])
        except EdgeGateError:
            missing.append(ref)
    return missing


def assert_refs_exist(store, kind: str, body: dict) -> None:
    for ref in direct_refs(kind, body):
        try:
            store.live_body(ref["to_kind"], ref["to_id"])
        except EdgeGateError as exc:
            raise EdgeGateError("invalid_reference", f"missing {ref['to_kind']}:{ref['to_id']}") from exc


def reference_report(store) -> dict:
    forward = all_forward_refs(store)
    reverse: dict[str, list[dict]] = {}
    for ref in forward:
        key = f"{ref['to_kind']}:{ref['to_id']}"
        reverse.setdefault(key, []).append(ref)
    return {
        "forward": forward,
        "reverse": {key: sorted(value, key=lambda r: (r["from_kind"], r["from_id"])) for key, value in sorted(reverse.items())},
        "dangling": missing_refs(store),
    }
