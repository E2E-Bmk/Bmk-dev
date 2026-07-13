"""Private durable JSON store for FlowLedger."""

from __future__ import annotations

import json
import os
import time
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any


STATE_FILE = "state.json"


def empty_state() -> dict[str, Any]:
    return {
        "version": 1,
        "sequence": 0,
        "counters": {"run": 0, "item": 0},
        "specs": {},
        "schedules": {},
        "runs": {},
        "steps": {},
        "attempts": [],
        "queue": [],
        "logs": [],
        "events": [],
        "recovery_markers": [],
    }


class JsonStore:
    """Small atomic JSON store.

    The public primitive modules accept either this object or a plain state
    dictionary. The facade uses this object so mutations are persisted after
    each operation.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file = self.path / STATE_FILE
        self.data: dict[str, Any] = empty_state()
        if self.file.exists():
            self.load()

    def init(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        if not self.file.exists():
            self.data = empty_state()
            self.save()
        else:
            self.load()

    def load(self) -> dict[str, Any]:
        self.path.mkdir(parents=True, exist_ok=True)
        if self.file.exists():
            with self.file.open("r", encoding="utf-8") as fh:
                self.data = json.load(fh)
        else:
            self.data = empty_state()
        ensure_shape(self.data)
        return self.data

    def save(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        ensure_shape(self.data)
        tmp = self.path / f".{STATE_FILE}.{uuid.uuid4().hex}.tmp"
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        last_error: OSError | None = None
        for _ in range(5):
            try:
                os.replace(tmp, self.file)
                return
            except OSError as exc:
                last_error = exc
                time.sleep(0.02)
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        if last_error:
            raise last_error

    def snapshot(self) -> dict[str, Any]:
        self.load()
        return deepcopy(self.data)

    def replace(self, data: dict[str, Any]) -> None:
        self.data = deepcopy(data)
        ensure_shape(self.data)
        self.save()

    def next_sequence(self) -> int:
        self.data["sequence"] = int(self.data.get("sequence", 0)) + 1
        return self.data["sequence"]

    def next_id(self, kind: str) -> str:
        counters = self.data.setdefault("counters", {})
        counters[kind] = int(counters.get(kind, 0)) + 1
        prefix = "run" if kind == "run" else "item"
        return f"{prefix}-{counters[kind]:06d}"


def state_of(store: Any) -> dict[str, Any]:
    if isinstance(store, dict):
        ensure_shape(store)
        return store
    data = getattr(store, "data", None)
    if isinstance(data, dict):
        ensure_shape(data)
        return data
    raise TypeError("store must be a JsonStore or state dictionary")


def save_if_possible(store: Any) -> None:
    save = getattr(store, "save", None)
    if callable(save):
        save()


def ensure_shape(data: dict[str, Any]) -> None:
    base = empty_state()
    for key, value in base.items():
        if key not in data:
            data[key] = deepcopy(value)
    data.setdefault("counters", {}).setdefault("run", 0)
    data.setdefault("counters", {}).setdefault("item", 0)


def next_sequence(store: Any) -> int:
    if hasattr(store, "next_sequence"):
        return store.next_sequence()
    data = state_of(store)
    data["sequence"] = int(data.get("sequence", 0)) + 1
    return data["sequence"]


def next_id(store: Any, kind: str) -> str:
    if hasattr(store, "next_id"):
        return store.next_id(kind)
    data = state_of(store)
    counters = data.setdefault("counters", {})
    counters[kind] = int(counters.get(kind, 0)) + 1
    prefix = "run" if kind == "run" else "item"
    return f"{prefix}-{counters[kind]:06d}"
