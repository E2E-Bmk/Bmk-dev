#!/usr/bin/env python3
"""
MiniRedis - a compact in-memory data structure store.
"""

import sys
import json
import shlex
import fnmatch
import time
from typing import Any, Dict, List, Optional, Set, Union

class CommandError(Exception):
    pass

class MiniRedisDB:
    def __init__(self):
        self.db: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> float:
        return time.time()

    def _clean_expired(self) -> None:
        now = self._now()
        to_del = [k for k, v in self.db.items() if v["expiry"] is not None and now >= v["expiry"]]
        for k in to_del:
            del self.db[k]

    def _get_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a key entry or None if missing/expired. Lazy removal on access."""
        entry = self.db.get(key)
        if entry is None:
            return None
        if entry["expiry"] is not None and self._now() >= entry["expiry"]:
            del self.db[key]
            return None
        return entry

    # Strings
    def set(self, key: str, value: str) -> str:
        self.db[key] = {"type": "string", "value": value, "expiry": None}
        return "OK"

    def get(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "(nil)"
        if entry["type"] != "string":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return entry["value"]

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            entry = self._get_key(k)
            if entry is not None:
                del self.db[k]
                count += 1
        return count

    def exists(self, key: str) -> int:
        return 1 if self._get_key(key) is not None else 0

    # Lists
    def lpush(self, key: str, *elements: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            entry = {"type": "list", "value": [], "expiry": None}
            self.db[key] = entry
        elif entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        lst: List[str] = entry["value"]
        for e in reversed(elements):
            lst.insert(0, e)
        return len(lst)

    def rpush(self, key: str, *elements: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            entry = {"type": "list", "value": [], "expiry": None}
            self.db[key] = entry
        elif entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        lst: List[str] = entry["value"]
        lst.extend(elements)
        return len(lst)

    def lpop(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "(nil)"
        if entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        lst: List[str] = entry["value"]
        if not lst:
            del self.db[key]
            return "(nil)"
        val = lst.pop(0)
        if not lst:
            del self.db[key]
        return val

    def rpop(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "(nil)"
        if entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        lst: List[str] = entry["value"]
        if not lst:
            del self.db[key]
            return "(nil)"
        val = lst.pop()
        if not lst:
            del self.db[key]
        return val

    def lrange(self, key: str, start: str, stop: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "[]"
        if entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        lst: List[str] = entry["value"]
        length = len(lst)
        if length == 0:
            return "[]"
        try:
            s = int(start)
            e = int(stop)
        except ValueError:
            raise CommandError("value is not an integer or out of range")
        # adjust negative indices
        if s < 0:
            s += length
        if s < 0:
            s = 0
        if e < 0:
            e += length
        if e < 0:
            e = 0
        if s > length - 1 or s > e:
            return "[]"
        if e > length - 1:
            e = length - 1
        sliced = lst[s:e+1]
        return json.dumps(sliced, separators=(',', ':'))

    def llen(self, key: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "list":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return len(entry["value"])

    # Sets
    def sadd(self, key: str, *members: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            entry = {"type": "set", "value": set(), "expiry": None}
            self.db[key] = entry
        elif entry["type"] != "set":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        s: Set[str] = entry["value"]
        added = 0
        for m in members:
            if m not in s:
                s.add(m)
                added += 1
        return added

    def srem(self, key: str, *members: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "set":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        s: Set[str] = entry["value"]
        removed = 0
        for m in members:
            if m in s:
                s.remove(m)
                removed += 1
        if not s:
            del self.db[key]
        return removed

    def smembers(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "[]"
        if entry["type"] != "set":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        members = sorted(entry["value"])
        return json.dumps(members, separators=(',', ':'))

    def sismember(self, key: str, member: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "set":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return 1 if member in entry["value"] else 0

    def scard(self, key: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "set":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return len(entry["value"])

    # Hashes
    def hset(self, key: str, *pairs: str) -> int:
        if len(pairs) % 2 != 0:
            raise CommandError("wrong number of arguments for HSET command")
        entry = self._get_key(key)
        if entry is None:
            entry = {"type": "hash", "value": {}, "expiry": None}
            self.db[key] = entry
        elif entry["type"] != "hash":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        h: Dict[str, str] = entry["value"]
        new_count = 0
        for i in range(0, len(pairs), 2):
            field = pairs[i]
            value = pairs[i+1]
            if field not in h:
                new_count += 1
            h[field] = value
        return new_count

    def hget(self, key: str, field: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "(nil)"
        if entry["type"] != "hash":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        h: Dict[str, str] = entry["value"]
        return h.get(field, "(nil)")

    def hdel(self, key: str, *fields: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "hash":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        h: Dict[str, str] = entry["value"]
        removed = 0
        for f in fields:
            if f in h:
                del h[f]
                removed += 1
        if not h:
            del self.db[key]
        return removed

    def hgetall(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "{}"
        if entry["type"] != "hash":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return json.dumps(entry["value"], separators=(',', ':'))

    def hexists(self, key: str, field: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return 0
        if entry["type"] != "hash":
            raise CommandError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return 1 if field in entry["value"] else 0

    # Key management
    def keys(self, pattern: Optional[str] = None) -> str:
        self._clean_expired()
        all_keys = list(self.db.keys())
        if pattern is None:
            matched = all_keys
        else:
            matched = [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        matched.sort()
        return json.dumps(matched, separators=(',', ':'))

    def type(self, key: str) -> str:
        entry = self._get_key(key)
        if entry is None:
            return "none"
        return entry["type"]

    def expire(self, key: str, seconds_str: str) -> int:
        try:
            seconds = int(seconds_str)
        except ValueError:
            raise CommandError("value is not an integer")
        entry = self._get_key(key)
        if entry is None:
            return 0
        entry["expiry"] = self._now() + seconds
        return 1

    def ttl(self, key: str) -> int:
        entry = self._get_key(key)
        if entry is None:
            return -2
        if entry["expiry"] is None:
            return -1
        remaining = int(entry["expiry"] - self._now())
        if remaining < 0:
            del self.db[key]
            return -2
        return remaining

    def flushdb(self) -> str:
        self.db.clear()
        return "OK"

    def dbsize(self) -> int:
        self._clean_expired()
        return len(self.db)


def process_command(db: MiniRedisDB, args: List[str]) -> str:
    """Execute a command and return the output string. Raises CommandError on failure."""
    if not args:
        return ""
    cmd = args[0].upper()

    if cmd == "SET":
        if len(args) != 3:
            raise CommandError("wrong number of arguments for 'SET' command")
        return db.set(args[1], args[2])

    elif cmd == "GET":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'GET' command")
        return db.get(args[1])

    elif cmd == "DEL":
        if len(args) < 2:
            raise CommandError("wrong number of arguments for 'DEL' command")
        return str(db.delete(*args[1:]))

    elif cmd == "EXISTS":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'EXISTS' command")
        return str(db.exists(args[1]))

    elif cmd == "LPUSH":
        if len(args) < 3:
            raise CommandError("wrong number of arguments for 'LPUSH' command")
        return str(db.lpush(args[1], *args[2:]))

    elif cmd == "RPUSH":
        if len(args) < 3:
            raise CommandError("wrong number of arguments for 'RPUSH' command")
        return str(db.rpush(args[1], *args[2:]))

    elif cmd == "LPOP":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'LPOP' command")
        return db.lpop(args[1])

    elif cmd == "RPOP":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'RPOP' command")
        return db.rpop(args[1])

    elif cmd == "LRANGE":
        if len(args) != 4:
            raise CommandError("wrong number of arguments for 'LRANGE' command")
        return db.lrange(args[1], args[2], args[3])

    elif cmd == "LLEN":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'LLEN' command")
        return str(db.llen(args[1]))

    elif cmd == "SADD":
        if len(args) < 3:
            raise CommandError("wrong number of arguments for 'SADD' command")
        return str(db.sadd(args[1], *args[2:]))

    elif cmd == "SREM":
        if len(args) < 3:
            raise CommandError("wrong number of arguments for 'SREM' command")
        return str(db.srem(args[1], *args[2:]))

    elif cmd == "SMEMBERS":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'SMEMBERS' command")
        return db.smembers(args[1])

    elif cmd == "SISMEMBER":
        if len(args) != 3:
            raise CommandError("wrong number of arguments for 'SISMEMBER' command")
        return str(db.sismember(args[1], args[2]))

    elif cmd == "SCARD":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'SCARD' command")
        return str(db.scard(args[1]))

    elif cmd == "HSET":
        if len(args) < 4 or (len(args) - 1) % 2 != 0:
            raise CommandError("wrong number of arguments for 'HSET' command")
        return str(db.hset(args[1], *args[2:]))

    elif cmd == "HGET":
        if len(args) != 3:
            raise CommandError("wrong number of arguments for 'HGET' command")
        return db.hget(args[1], args[2])

    elif cmd == "HDEL":
        if len(args) < 3:
            raise CommandError("wrong number of arguments for 'HDEL' command")
        return str(db.hdel(args[1], *args[2:]))

    elif cmd == "HGETALL":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'HGETALL' command")
        return db.hgetall(args[1])

    elif cmd == "HEXISTS":
        if len(args) != 3:
            raise CommandError("wrong number of arguments for 'HEXISTS' command")
        return str(db.hexists(args[1], args[2]))

    elif cmd == "KEYS":
        if len(args) > 2:
            raise CommandError("wrong number of arguments for 'KEYS' command")
        pattern = args[1] if len(args) == 2 else None
        return db.keys(pattern)

    elif cmd == "TYPE":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'TYPE' command")
        return json.dumps(db.type(args[1]))

    elif cmd == "EXPIRE":
        if len(args) != 3:
            raise CommandError("wrong number of arguments for 'EXPIRE' command")
        return str(db.expire(args[1], args[2]))

    elif cmd == "TTL":
        if len(args) != 2:
            raise CommandError("wrong number of arguments for 'TTL' command")
        return str(db.ttl(args[1]))

    elif cmd == "FLUSHDB":
        if len(args) != 1:
            raise CommandError("wrong number of arguments for 'FLUSHDB' command")
        return db.flushdb()

    elif cmd == "DBSIZE":
        if len(args) != 1:
            raise CommandError("wrong number of arguments for 'DBSIZE' command")
        return str(db.dbsize())

    else:
        raise CommandError(f"unknown command '{cmd}'")


def main() -> None:
    if len(sys.argv) < 2:
        # No arguments: just exit silently
        return

    db = MiniRedisDB()

    if sys.argv[1] == '--batch':
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                parts = shlex.split(line)
            except ValueError as e:
                print(f"Error parsing command: {e}", file=sys.stderr)
                continue
            try:
                result = process_command(db, parts)
                print(result)
            except CommandError as e:
                print(f"(error) {e}", file=sys.stderr)
    else:
        args = sys.argv[1:]
        try:
            result = process_command(db, args)
            print(result)
        except CommandError as e:
            print(f"(error) {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
