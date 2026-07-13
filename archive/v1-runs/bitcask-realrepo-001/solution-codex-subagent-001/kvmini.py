#!/usr/bin/env python3
"""MiniBitcask: a tiny append-only disk-backed key/value store."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


SEGMENT_PREFIX = "segment-"
SEGMENT_SUFFIX = ".log"
DEFAULT_MAX_SEGMENT_BYTES = 1024 * 1024


class StoreError(Exception):
    pass


class MiniBitcask:
    def __init__(self, dbdir: Path) -> None:
        self.dbdir = dbdir
        self.dbdir.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, str] = {}
        self.log_entries = 0
        self._load()

    def _segments(self) -> list[Path]:
        return sorted(
            p
            for p in self.dbdir.iterdir()
            if p.is_file() and p.name.startswith(SEGMENT_PREFIX) and p.name.endswith(SEGMENT_SUFFIX)
        )

    def _load(self) -> None:
        self.data.clear()
        self.log_entries = 0
        for segment in self._segments():
            with segment.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    op = record.get("op")
                    key = record.get("key")
                    if not isinstance(key, str):
                        continue
                    if op == "put":
                        value = record.get("value")
                        if not isinstance(value, str):
                            continue
                        self.data[key] = value
                        self.log_entries += 1
                    elif op == "del":
                        self.data.pop(key, None)
                        self.log_entries += 1

    def _max_segment_bytes(self) -> int:
        raw = os.environ.get("KVMINI_MAX_SEGMENT_BYTES")
        if raw is None:
            return DEFAULT_MAX_SEGMENT_BYTES
        try:
            return max(1, int(raw))
        except ValueError:
            return DEFAULT_MAX_SEGMENT_BYTES

    def _next_segment_index(self) -> int:
        highest = -1
        for segment in self._segments():
            stem = segment.name[len(SEGMENT_PREFIX) : -len(SEGMENT_SUFFIX)]
            try:
                highest = max(highest, int(stem))
            except ValueError:
                continue
        return highest + 1

    def _active_segment(self, record_bytes: bytes) -> Path:
        segments = self._segments()
        if not segments:
            return self.dbdir / f"{SEGMENT_PREFIX}000000{SEGMENT_SUFFIX}"

        active = segments[-1]
        size = active.stat().st_size
        if size > 0 and size + len(record_bytes) > self._max_segment_bytes():
            return self.dbdir / f"{SEGMENT_PREFIX}{self._next_segment_index():06d}{SEGMENT_SUFFIX}"
        return active

    def _append(self, record: dict[str, Any]) -> None:
        payload = (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        segment = self._active_segment(payload)
        with segment.open("ab") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        self.log_entries += 1

    def put(self, key: str, value: str) -> None:
        self._append({"op": "put", "key": key, "value": value})
        self.data[key] = value

    def update(self, key: str, value: str) -> None:
        if key not in self.data:
            raise StoreError(f"missing key: {key}")
        self.put(key, value)

    def get(self, key: str) -> str:
        if key not in self.data:
            raise StoreError(f"missing key: {key}")
        return self.data[key]

    def delete(self, key: str) -> None:
        if key not in self.data:
            raise StoreError(f"missing key: {key}")
        self._append({"op": "del", "key": key})
        del self.data[key]

    def keys(self) -> list[str]:
        return sorted(self.data)

    def list_items(self) -> dict[str, str]:
        return {key: self.data[key] for key in sorted(self.data)}

    def stats(self) -> dict[str, int]:
        return {"live_keys": len(self.data), "log_entries": self.log_entries}

    def compact(self) -> None:
        tmpdir = Path(tempfile.mkdtemp(prefix=".compact-", dir=self.dbdir))
        tmp_segment = tmpdir / f"{SEGMENT_PREFIX}000000{SEGMENT_SUFFIX}"
        try:
            with tmp_segment.open("wb") as fh:
                for key in sorted(self.data):
                    payload = (
                        json.dumps(
                            {"op": "put", "key": key, "value": self.data[key]},
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        + "\n"
                    ).encode("utf-8")
                    fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())

            final_segment = self.dbdir / f"{SEGMENT_PREFIX}000000{SEGMENT_SUFFIX}"
            for segment in self._segments():
                segment.unlink()
            os.replace(tmp_segment, final_segment)
            try:
                os.rmdir(tmpdir)
            except OSError:
                pass
            self.log_entries = len(self.data)
        finally:
            if tmpdir.exists():
                for child in tmpdir.iterdir():
                    child.unlink()
                try:
                    os.rmdir(tmpdir)
                except OSError:
                    pass


def dump_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def usage() -> str:
    return (
        "usage: kvmini.py DBDIR COMMAND [ARGS...]\n"
        "commands: put KEY VALUE | update KEY VALUE | get KEY | mget KEY [KEY...] | "
        "delete KEY | keys | count | list | stats | compact"
    )


def require_arity(args: list[str], expected: int) -> None:
    if len(args) != expected:
        raise StoreError(usage())


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(usage(), file=sys.stderr)
        return 2

    dbdir = Path(argv[1])
    command = argv[2]
    args = argv[3:]

    try:
        store = MiniBitcask(dbdir)

        if command == "put":
            require_arity(args, 2)
            store.put(args[0], args[1])
            print("OK")
        elif command == "update":
            require_arity(args, 2)
            store.update(args[0], args[1])
            print("OK")
        elif command == "get":
            require_arity(args, 1)
            print(store.get(args[0]))
        elif command == "mget":
            if len(args) < 1:
                raise StoreError(usage())
            dump_json({key: store.data[key] for key in args if key in store.data})
        elif command == "delete":
            require_arity(args, 1)
            store.delete(args[0])
            print("OK")
        elif command == "keys":
            require_arity(args, 0)
            dump_json(store.keys())
        elif command == "count":
            require_arity(args, 0)
            print(len(store.data))
        elif command == "list":
            require_arity(args, 0)
            dump_json(store.list_items())
        elif command == "stats":
            require_arity(args, 0)
            dump_json(store.stats())
        elif command == "compact":
            require_arity(args, 0)
            store.compact()
            print("OK")
        else:
            raise StoreError(usage())
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
