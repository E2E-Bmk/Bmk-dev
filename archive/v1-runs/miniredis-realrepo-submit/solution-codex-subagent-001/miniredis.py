#!/usr/bin/env python3
"""A compact in-memory Redis-like CLI store."""

from __future__ import annotations

import fnmatch
import json
import math
import shlex
import sys
import time
from dataclasses import dataclass
from typing import Any


NIL = "(nil)"


class MiniRedisError(Exception):
    """User-facing command error."""


@dataclass
class Entry:
    type: str
    value: Any
    expires_at: float | None = None


class MiniRedis:
    def __init__(self) -> None:
        self._db: dict[str, Entry] = {}

    def execute(self, argv: list[str]) -> str | None:
        if not argv:
            return None

        command = argv[0].lstrip("\ufeff\ufffe").upper()
        args = argv[1:]
        handler = getattr(self, f"_cmd_{command.lower()}", None)
        if handler is None:
            raise MiniRedisError(f"unknown command: {argv[0]}")
        return handler(args)

    def _purge_if_expired(self, key: str) -> bool:
        entry = self._db.get(key)
        if entry is None:
            return False
        if entry.expires_at is not None and entry.expires_at <= time.time():
            del self._db[key]
            return True
        return False

    def _get_entry(self, key: str) -> Entry | None:
        self._purge_if_expired(key)
        return self._db.get(key)

    def _require_type(self, key: str, expected: str) -> Entry | None:
        entry = self._get_entry(key)
        if entry is None:
            return None
        if entry.type != expected:
            raise MiniRedisError(
                f"wrong type for key '{key}': expected {expected}, found {entry.type}"
            )
        return entry

    def _live_keys(self) -> list[str]:
        for key in list(self._db):
            self._purge_if_expired(key)
        return list(self._db)

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _require_arg_count(args: list[str], minimum: int, maximum: int | None = None) -> None:
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            if maximum is None:
                raise MiniRedisError(f"expected at least {minimum} argument(s)")
            if minimum == maximum:
                raise MiniRedisError(f"expected {minimum} argument(s)")
            raise MiniRedisError(f"expected between {minimum} and {maximum} argument(s)")

    def _cmd_set(self, args: list[str]) -> str:
        self._require_arg_count(args, 2, 2)
        key, value = args
        self._db[key] = Entry("string", value)
        return "OK"

    def _cmd_get(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "string")
        return NIL if entry is None else entry.value

    def _cmd_del(self, args: list[str]) -> str:
        self._require_arg_count(args, 1)
        removed = 0
        for key in args:
            self._purge_if_expired(key)
            if key in self._db:
                del self._db[key]
                removed += 1
        return str(removed)

    def _cmd_exists(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        return "1" if self._get_entry(args[0]) is not None else "0"

    def _list_for_write(self, key: str) -> list[str]:
        entry = self._require_type(key, "list")
        if entry is None:
            value: list[str] = []
            self._db[key] = Entry("list", value)
            return value
        return entry.value

    def _cmd_lpush(self, args: list[str]) -> str:
        self._require_arg_count(args, 2)
        values = self._list_for_write(args[0])
        for element in args[1:]:
            values.insert(0, element)
        return str(len(values))

    def _cmd_rpush(self, args: list[str]) -> str:
        self._require_arg_count(args, 2)
        values = self._list_for_write(args[0])
        values.extend(args[1:])
        return str(len(values))

    def _cmd_lpop(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "list")
        if entry is None or not entry.value:
            return NIL
        return entry.value.pop(0)

    def _cmd_rpop(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "list")
        if entry is None or not entry.value:
            return NIL
        return entry.value.pop()

    def _cmd_lrange(self, args: list[str]) -> str:
        self._require_arg_count(args, 3, 3)
        try:
            start = int(args[1])
            stop = int(args[2])
        except ValueError as exc:
            raise MiniRedisError("LRANGE start and stop must be integers") from exc

        entry = self._require_type(args[0], "list")
        if entry is None:
            return "[]"

        values = entry.value
        length = len(values)
        if start < 0:
            start += length
        if stop < 0:
            stop += length
        start = max(start, 0)
        stop = min(stop, length - 1)
        if start > stop or start >= length:
            return "[]"
        return self._json(values[start : stop + 1])

    def _cmd_llen(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "list")
        return "0" if entry is None else str(len(entry.value))

    def _set_for_write(self, key: str) -> set[str]:
        entry = self._require_type(key, "set")
        if entry is None:
            value: set[str] = set()
            self._db[key] = Entry("set", value)
            return value
        return entry.value

    def _cmd_sadd(self, args: list[str]) -> str:
        self._require_arg_count(args, 2)
        values = self._set_for_write(args[0])
        before = len(values)
        values.update(args[1:])
        return str(len(values) - before)

    def _cmd_srem(self, args: list[str]) -> str:
        self._require_arg_count(args, 2)
        entry = self._require_type(args[0], "set")
        if entry is None:
            return "0"
        removed = 0
        for member in args[1:]:
            if member in entry.value:
                entry.value.remove(member)
                removed += 1
        return str(removed)

    def _cmd_smembers(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "set")
        if entry is None:
            return "[]"
        return self._json(sorted(entry.value))

    def _cmd_sismember(self, args: list[str]) -> str:
        self._require_arg_count(args, 2, 2)
        entry = self._require_type(args[0], "set")
        return "1" if entry is not None and args[1] in entry.value else "0"

    def _cmd_scard(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "set")
        return "0" if entry is None else str(len(entry.value))

    def _hash_for_write(self, key: str) -> dict[str, str]:
        entry = self._require_type(key, "hash")
        if entry is None:
            value: dict[str, str] = {}
            self._db[key] = Entry("hash", value)
            return value
        return entry.value

    def _cmd_hset(self, args: list[str]) -> str:
        self._require_arg_count(args, 3)
        if len(args[1:]) % 2 != 0:
            raise MiniRedisError("HSET requires field/value pairs")
        values = self._hash_for_write(args[0])
        added = 0
        pairs = args[1:]
        for index in range(0, len(pairs), 2):
            field, value = pairs[index], pairs[index + 1]
            if field not in values:
                added += 1
            values[field] = value
        return str(added)

    def _cmd_hget(self, args: list[str]) -> str:
        self._require_arg_count(args, 2, 2)
        entry = self._require_type(args[0], "hash")
        if entry is None:
            return NIL
        return entry.value.get(args[1], NIL)

    def _cmd_hdel(self, args: list[str]) -> str:
        self._require_arg_count(args, 2)
        entry = self._require_type(args[0], "hash")
        if entry is None:
            return "0"
        removed = 0
        for field in args[1:]:
            if field in entry.value:
                del entry.value[field]
                removed += 1
        return str(removed)

    def _cmd_hgetall(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._require_type(args[0], "hash")
        if entry is None:
            return "{}"
        return self._json(dict(sorted(entry.value.items())))

    def _cmd_hexists(self, args: list[str]) -> str:
        self._require_arg_count(args, 2, 2)
        entry = self._require_type(args[0], "hash")
        return "1" if entry is not None and args[1] in entry.value else "0"

    def _cmd_keys(self, args: list[str]) -> str:
        self._require_arg_count(args, 0, 1)
        pattern = args[0] if args else "*"
        keys = sorted(key for key in self._live_keys() if fnmatch.fnmatchcase(key, pattern))
        return self._json(keys)

    def _cmd_type(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._get_entry(args[0])
        return "none" if entry is None else entry.type

    def _cmd_expire(self, args: list[str]) -> str:
        self._require_arg_count(args, 2, 2)
        try:
            seconds = int(args[1])
        except ValueError as exc:
            raise MiniRedisError("EXPIRE seconds must be an integer") from exc
        entry = self._get_entry(args[0])
        if entry is None:
            return "0"
        entry.expires_at = time.time() + seconds
        return "1"

    def _cmd_ttl(self, args: list[str]) -> str:
        self._require_arg_count(args, 1, 1)
        entry = self._get_entry(args[0])
        if entry is None:
            return "-2"
        if entry.expires_at is None:
            return "-1"
        remaining = math.ceil(entry.expires_at - time.time())
        if remaining <= 0:
            self._purge_if_expired(args[0])
            return "-2"
        return str(remaining)

    def _cmd_flushdb(self, args: list[str]) -> str:
        self._require_arg_count(args, 0, 0)
        self._db.clear()
        return "OK"

    def _cmd_dbsize(self, args: list[str]) -> str:
        self._require_arg_count(args, 0, 0)
        return str(len(self._live_keys()))


def run_one_shot(argv: list[str]) -> int:
    redis = MiniRedis()
    try:
        result = redis.execute(argv)
    except MiniRedisError as exc:
        print(f"ERR {exc}", file=sys.stderr)
        return 1
    if result is not None:
        print(result)
    return 0


def run_batch() -> int:
    redis = MiniRedis()
    try:
        sys.stdin.reconfigure(encoding="utf-8-sig")
    except AttributeError:
        pass
    for line_number, line in enumerate(sys.stdin, start=1):
        line = line.strip().lstrip("\ufeff")
        if not line:
            continue
        try:
            argv = shlex.split(line)
            result = redis.execute(argv)
        except ValueError as exc:
            print(f"ERR line {line_number}: {exc}", file=sys.stderr)
            continue
        except MiniRedisError as exc:
            print(f"ERR line {line_number}: {exc}", file=sys.stderr)
            continue
        if result is not None:
            print(result)
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--batch":
        if len(argv) != 1:
            print("ERR --batch does not accept command arguments", file=sys.stderr)
            return 1
        return run_batch()
    if not argv:
        print("ERR missing command", file=sys.stderr)
        return 1
    return run_one_shot(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
