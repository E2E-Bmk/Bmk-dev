from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import COLLECTIONS, KINDS, EdgeGateError, ResourceRecord, clone, digest_value, ensure_kind


class ResourceStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.records: dict[str, dict[str, ResourceRecord]] = {kind: {} for kind in KINDS}
        self.audit: list[dict[str, Any]] = []
        self.generation = 0
        self.config_digest = digest_value({})
        self.counters: dict[str, int] = {}
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.generation = data.get("generation", 0)
        self.config_digest = data.get("config_digest", digest_value({}))
        self.audit = data.get("audit", [])
        self.counters = data.get("counters", {})
        for kind in KINDS:
            self.records[kind] = {}
            for rid, rec in data.get("records", {}).get(kind, {}).items():
                self.records[kind][rid] = ResourceRecord(
                    kind=kind,
                    id=rid,
                    body=rec["body"],
                    version=rec["version"],
                    digest=rec["digest"],
                    updated_at=rec.get("updated_at"),
                    tombstone=rec.get("tombstone", False),
                )

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "generation": self.generation,
            "config_digest": self.config_digest,
            "audit": self.audit,
            "counters": self.counters,
            "records": {
                kind: {rid: rec.public() for rid, rec in rows.items()}
                for kind, rows in self.records.items()
            },
        }
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def append_audit(self, action: str, kind: str | None, rid: str | None, now=None, **extra) -> None:
        entry = {
            "seq": len(self.audit) + 1,
            "action": action,
            "kind": kind,
            "id": rid,
            "at": now,
        }
        entry.update(extra)
        self.audit.append(entry)

    def live(self, kind: str) -> list[ResourceRecord]:
        ensure_kind(kind)
        return [rec for rec in self.records[kind].values() if not rec.tombstone]

    def live_body(self, kind: str, rid: str) -> dict[str, Any]:
        rec = self.get_record(kind, rid)
        if rec.tombstone:
            raise EdgeGateError("not_found", f"{kind}:{rid} is deleted")
        return clone(rec.body)

    def get_record(self, kind: str, rid: str) -> ResourceRecord:
        ensure_kind(kind)
        rec = self.records[kind].get(rid)
        if rec is None:
            raise EdgeGateError("not_found", f"{kind}:{rid} not found")
        return rec

    def put_record(self, kind: str, rid: str, body: dict[str, Any], now=None) -> ResourceRecord:
        ensure_kind(kind)
        digest = digest_value(body)
        old = self.records[kind].get(rid)
        if old and not old.tombstone and old.digest == digest:
            self.append_audit("noop_put", kind, rid, now, version=old.version, digest=digest)
            self.save()
            return old
        version = 1 if old is None else old.version + 1
        rec = ResourceRecord(kind, rid, clone(body), version, digest, now, False)
        self.records[kind][rid] = rec
        self.append_audit("put", kind, rid, now, version=version, digest=digest)
        self.save()
        return rec

    def tombstone(self, kind: str, rid: str, now=None, *, force=False, dangling=None) -> ResourceRecord:
        old = self.get_record(kind, rid)
        if old.tombstone:
            self.append_audit("noop_delete", kind, rid, now, version=old.version)
            self.save()
            return old
        rec = ResourceRecord(kind, rid, clone(old.body), old.version + 1, old.digest, now, True)
        self.records[kind][rid] = rec
        self.append_audit("force_delete" if force else "delete", kind, rid, now, version=rec.version, dangling=dangling or [])
        self.save()
        return rec

    def live_document(self) -> dict[str, list[dict[str, Any]]]:
        return {
            collection: [clone(rec.body) for rec in sorted(self.live(kind), key=lambda r: r.id)]
            for kind, collection in COLLECTIONS.items()
        }
