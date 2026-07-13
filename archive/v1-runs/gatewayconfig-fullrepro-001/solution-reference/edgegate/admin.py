from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import COLLECTIONS, KINDS, EdgeGateError, clone, digest_value, ensure_kind
from .patches import merge_patch
from .references import assert_refs_exist, reference_report, reverse_refs
from .schemas import normalize_resource
from .store import ResourceStore


class EdgeGate:
    def __init__(self, path: str | Path | None = None):
        self.store = ResourceStore(path)

    def put(self, kind: str, resource_id: str, body: dict[str, Any], now=None) -> dict[str, Any]:
        normalized = normalize_resource(kind, resource_id, body)
        assert_refs_exist(self.store, kind, normalized)
        rec = self.store.put_record(kind, resource_id, normalized, now)
        self._refresh_config_digest()
        return rec.public()

    def patch(self, kind: str, resource_id: str, patch: dict[str, Any], now=None) -> dict[str, Any]:
        current = self.store.live_body(kind, resource_id)
        merged = merge_patch(current, patch)
        return self.put(kind, resource_id, merged, now=now)

    def delete(self, kind: str, resource_id: str, *, force: bool = False, now=None) -> dict[str, Any]:
        ensure_kind(kind)
        refs = reverse_refs(self.store, kind, resource_id)
        if refs and not force:
            raise EdgeGateError("reference_conflict", f"{kind}:{resource_id} is referenced")
        rec = self.store.tombstone(kind, resource_id, now, force=force, dangling=refs if force else [])
        self._refresh_config_digest()
        return rec.public()

    def get(self, kind: str, resource_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        rec = self.store.get_record(kind, resource_id)
        if rec.tombstone and not include_deleted:
            raise EdgeGateError("not_found", f"{kind}:{resource_id} is deleted")
        return rec.public()

    def list(self, kind: str, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        ensure_kind(kind)
        rows = self.store.records[kind].values() if include_deleted else self.store.live(kind)
        return [rec.public() for rec in sorted(rows, key=lambda r: r.id)]

    def load_standalone(self, document: dict[str, Any], now=None) -> dict[str, Any]:
        if not isinstance(document, dict):
            raise EdgeGateError("standalone_rejected", "standalone document must be an object")
        temp = EdgeGate()
        normalized_by_kind: dict[str, dict[str, dict[str, Any]]] = {kind: {} for kind in KINDS}
        try:
            for kind, collection in COLLECTIONS.items():
                rows = document.get(collection, [])
                if rows is None:
                    rows = []
                if not isinstance(rows, list):
                    raise EdgeGateError("invalid_resource", f"{collection} must be a list")
                for row in rows:
                    if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                        raise EdgeGateError("invalid_resource", f"{collection} row requires id")
                    normalized = normalize_resource(kind, row["id"], row)
                    normalized_by_kind[kind][row["id"]] = normalized
                    temp.store.put_record(kind, row["id"], normalized, now)
            for kind in KINDS:
                for rid, body in normalized_by_kind[kind].items():
                    assert_refs_exist(temp.store, kind, body)
        except EdgeGateError as exc:
            raise EdgeGateError("standalone_rejected", exc.code) from exc

        old_digest = self.store.config_digest
        changed = False
        for kind in KINDS:
            incoming_ids = set(normalized_by_kind[kind])
            for rid, body in normalized_by_kind[kind].items():
                before = self.store.records[kind].get(rid)
                rec = self.store.put_record(kind, rid, body, now)
                changed = changed or before is None or before.digest != rec.digest or before.tombstone
            for rec in list(self.store.live(kind)):
                if rec.id not in incoming_ids:
                    self.store.tombstone(kind, rec.id, now, force=True)
                    changed = True
        self._refresh_config_digest()
        if changed and self.store.config_digest != old_digest:
            self.store.generation += 1
            self.store.append_audit("standalone_reload", None, None, now, generation=self.store.generation, digest=self.store.config_digest)
        else:
            self.store.append_audit("noop_standalone_reload", None, None, now, generation=self.store.generation, digest=self.store.config_digest)
        self.store.save()
        return {"generation": self.store.generation, "digest": self.store.config_digest, "changed": self.store.config_digest != old_digest}

    def export_standalone(self) -> dict[str, list[dict[str, Any]]]:
        return self.store.live_document()

    def config_report(self) -> dict[str, Any]:
        from .reports import config_report

        return config_report(self)

    def reference_report(self) -> dict[str, Any]:
        return reference_report(self.store)

    def runtime_report(self) -> dict[str, Any]:
        from .reports import runtime_report

        return runtime_report(self)

    def audit_report(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        from .reports import audit_report

        return audit_report(self, include_deleted=include_deleted)

    def simulate_request(self, method: str, host: str, path: str, headers=None) -> dict[str, Any]:
        from .runtime import simulate_request

        return simulate_request(self, method, host, path, headers=headers)

    def _refresh_config_digest(self) -> None:
        self.store.config_digest = digest_value(self.export_standalone())
        self.store.save()
