from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any


KINDS = ("upstream", "service", "plugin_config", "global_rule", "route")
COLLECTIONS = {
    "upstream": "upstreams",
    "service": "services",
    "plugin_config": "plugin_configs",
    "global_rule": "global_rules",
    "route": "routes",
}


class EdgeGateError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


@dataclass
class ResourceRecord:
    kind: str
    id: str
    body: dict[str, Any]
    version: int
    digest: str
    updated_at: str | None = None
    tombstone: bool = False

    def public(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "id": self.id,
            "version": self.version,
            "digest": self.digest,
            "updated_at": self.updated_at,
            "tombstone": self.tombstone,
            "body": copy.deepcopy(self.body),
        }


def clone(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ensure_kind(kind: str) -> None:
    if kind not in KINDS:
        raise EdgeGateError("invalid_resource", f"unknown resource kind {kind}")
