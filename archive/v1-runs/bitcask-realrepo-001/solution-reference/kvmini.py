#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


DEFAULT_SEGMENT_BYTES = 1024 * 1024


class Store:
    def __init__(self, dbdir):
        self.dbdir = Path(dbdir)
        self.dbdir.mkdir(parents=True, exist_ok=True)
        self.live = {}
        self.log_entries = 0
        self._load()

    def _segment_paths(self):
        return sorted(self.dbdir.glob("*.jsonl"))

    def _load(self):
        self.live = {}
        self.log_entries = 0
        for path in self._segment_paths():
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    self.log_entries += 1
                    op = record.get("op")
                    key = record.get("key")
                    if op == "put":
                        self.live[key] = record.get("value", "")
                    elif op == "delete":
                        self.live.pop(key, None)

    def _max_segment_bytes(self):
        raw = os.environ.get("KVMINI_MAX_SEGMENT_BYTES")
        if raw is None:
            return DEFAULT_SEGMENT_BYTES
        try:
            return max(1, int(raw))
        except ValueError:
            return DEFAULT_SEGMENT_BYTES

    def _active_segment(self):
        paths = self._segment_paths()
        if not paths:
            return self.dbdir / "000001.jsonl"
        active = paths[-1]
        if active.stat().st_size >= self._max_segment_bytes():
            number = int(active.stem) + 1 if active.stem.isdigit() else len(paths) + 1
            return self.dbdir / f"{number:06d}.jsonl"
        return active

    def append(self, record):
        path = self._active_segment()
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        if record["op"] == "put":
            self.live[record["key"]] = record["value"]
        elif record["op"] == "delete":
            self.live.pop(record["key"], None)
        self.log_entries += 1

    def compact(self):
        tmp = self.dbdir / "compact.tmp"
        records = [{"op": "put", "key": key, "value": self.live[key]} for key in sorted(self.live)]
        with tmp.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

        for path in self._segment_paths():
            path.unlink()
        os.replace(tmp, self.dbdir / "000001.jsonl")
        self.log_entries = len(records)


def emit_json(value):
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def fail(message):
    print(message, file=sys.stderr)
    return 1


def require_args(args, count, usage):
    if len(args) != count:
        raise ValueError(f"usage: {usage}")


def main(argv):
    if len(argv) < 3:
        return fail("usage: kvmini.py DBDIR COMMAND [ARGS...]")

    dbdir = argv[1]
    command = argv[2]
    args = argv[3:]

    try:
        store = Store(dbdir)

        if command == "put":
            require_args(args, 2, "put KEY VALUE")
            store.append({"op": "put", "key": args[0], "value": args[1]})
            return 0

        if command == "update":
            require_args(args, 2, "update KEY VALUE")
            key, value = args
            if key not in store.live:
                return fail(f"missing key: {key}")
            store.append({"op": "put", "key": key, "value": value})
            return 0

        if command == "get":
            require_args(args, 1, "get KEY")
            key = args[0]
            if key not in store.live:
                return fail(f"missing key: {key}")
            print(store.live[key])
            return 0

        if command == "mget":
            if not args:
                raise ValueError("usage: mget KEY [KEY...]")
            emit_json({key: store.live[key] for key in args if key in store.live})
            return 0

        if command == "delete":
            require_args(args, 1, "delete KEY")
            key = args[0]
            if key not in store.live:
                return fail(f"missing key: {key}")
            store.append({"op": "delete", "key": key})
            return 0

        if command == "keys":
            require_args(args, 0, "keys")
            emit_json(sorted(store.live))
            return 0

        if command == "count":
            require_args(args, 0, "count")
            print(len(store.live))
            return 0

        if command == "list":
            require_args(args, 0, "list")
            emit_json({key: store.live[key] for key in sorted(store.live)})
            return 0

        if command == "stats":
            require_args(args, 0, "stats")
            emit_json({"live_keys": len(store.live), "log_entries": store.log_entries})
            return 0

        if command == "compact":
            require_args(args, 0, "compact")
            store.compact()
            return 0

        return fail(f"unknown command: {command}")
    except ValueError as exc:
        return fail(str(exc))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"store error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
