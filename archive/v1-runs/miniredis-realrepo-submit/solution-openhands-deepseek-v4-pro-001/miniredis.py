#!/usr/bin/env python3
"""miniredis - A compact in-memory data structure store."""

import sys
import json
import time
import fnmatch


class MiniRedisDB:
    """In-memory database supporting strings, lists, sets, and hashes with TTL."""

    def __init__(self):
        self._store = {}  # key -> {"type": type, "value": value, "expires_at": float|None}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _now(self):
        return time.time()

    def _is_expired(self, key):
        entry = self._store.get(key)
        if entry is None:
            return True  # non-existent treated as expired
        if entry["expires_at"] is not None and self._now() >= entry["expires_at"]:
            del self._store[key]
            return True
        return False

    def _get_entry(self, key):
        """Return entry if key exists and is live, else None."""
        if self._is_expired(key):
            return None
        return self._store.get(key)

    def _get_type(self, key):
        entry = self._get_entry(key)
        return entry["type"] if entry else "none"

    def _check_type(self, key, expected_type, cmd_name):
        """Return (ok, error_message). If type mismatch, error is non-empty."""
        entry = self._get_entry(key)
        if entry is None:
            return True, None
        if entry["type"] != expected_type:
            return False, f"WRONGTYPE Operation against a key holding the wrong kind of value"
        return True, None

    # ------------------------------------------------------------------
    # String Operations
    # ------------------------------------------------------------------

    def cmd_set(self, key, value):
        self._store[key] = {"type": "string", "value": str(value), "expires_at": None}
        return "OK"

    def cmd_get(self, key):
        entry = self._get_entry(key)
        if entry is None:
            return "(nil)"
        if entry["type"] != "string":
            return (False, f"WRONGTYPE Operation against a key holding the wrong kind of value")
        return entry["value"]

    def cmd_del(self, *keys):
        count = 0
        for key in keys:
            if not self._is_expired(key) and key in self._store:
                del self._store[key]
                count += 1
        return count

    def cmd_exists(self, key):
        entry = self._get_entry(key)
        return 1 if entry else 0

    # ------------------------------------------------------------------
    # List Operations
    # ------------------------------------------------------------------

    def cmd_lpush(self, key, *elements):
        ok, err = self._check_type(key, "list", "LPUSH")
        if not ok:
            return (False, err)
        if key not in self._store or self._is_expired(key):
            self._store[key] = {"type": "list", "value": [], "expires_at": None}
        lst = self._store[key]["value"]
        for elem in reversed(elements):
            lst.insert(0, str(elem))
        return len(lst)

    def cmd_rpush(self, key, *elements):
        ok, err = self._check_type(key, "list", "RPUSH")
        if not ok:
            return (False, err)
        if key not in self._store or self._is_expired(key):
            self._store[key] = {"type": "list", "value": [], "expires_at": None}
        lst = self._store[key]["value"]
        for elem in elements:
            lst.append(str(elem))
        return len(lst)

    def cmd_lpop(self, key):
        ok, err = self._check_type(key, "list", "LPOP")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return "(nil)"
        lst = entry["value"]
        if not lst:
            return "(nil)"
        val = lst.pop(0)
        return val

    def cmd_rpop(self, key):
        ok, err = self._check_type(key, "list", "RPOP")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return "(nil)"
        lst = entry["value"]
        if not lst:
            return "(nil)"
        val = lst.pop()
        return val

    def cmd_lrange(self, key, start, stop):
        ok, err = self._check_type(key, "list", "LRANGE")
        if not ok:
            return (False, err)
        try:
            start = int(start)
            stop = int(stop)
        except (ValueError, TypeError):
            return (False, "value is not an integer or out of range")
        entry = self._get_entry(key)
        if entry is None:
            return json.dumps([])
        lst = entry["value"]
        length = len(lst)
        # Handle negative indices
        if start < 0:
            start = max(length + start, 0)
        if stop < 0:
            stop = length + stop
        # Slice inclusive
        result = lst[max(start, 0):stop + 1]
        return json.dumps(result)

    def cmd_llen(self, key):
        ok, err = self._check_type(key, "list", "LLEN")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        return len(entry["value"])

    # ------------------------------------------------------------------
    # Set Operations
    # ------------------------------------------------------------------

    def cmd_sadd(self, key, *members):
        ok, err = self._check_type(key, "set", "SADD")
        if not ok:
            return (False, err)
        if key not in self._store or self._is_expired(key):
            self._store[key] = {"type": "set", "value": set(), "expires_at": None}
        s = self._store[key]["value"]
        added = 0
        for m in members:
            m = str(m)
            if m not in s:
                s.add(m)
                added += 1
        return added

    def cmd_srem(self, key, *members):
        ok, err = self._check_type(key, "set", "SREM")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        s = entry["value"]
        removed = 0
        for m in members:
            m = str(m)
            if m in s:
                s.remove(m)
                removed += 1
        return removed

    def cmd_smembers(self, key):
        ok, err = self._check_type(key, "set", "SMEMBERS")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return json.dumps([])
        return json.dumps(sorted(list(entry["value"])))

    def cmd_sismember(self, key, member):
        ok, err = self._check_type(key, "set", "SISMEMBER")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        return 1 if str(member) in entry["value"] else 0

    def cmd_scard(self, key):
        ok, err = self._check_type(key, "set", "SCARD")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        return len(entry["value"])

    # ------------------------------------------------------------------
    # Hash Operations
    # ------------------------------------------------------------------

    def cmd_hset(self, key, *args):
        if len(args) % 2 != 0:
            return (False, "wrong number of arguments for 'HSET' command")
        ok, err = self._check_type(key, "hash", "HSET")
        if not ok:
            return (False, err)
        if key not in self._store or self._is_expired(key):
            self._store[key] = {"type": "hash", "value": {}, "expires_at": None}
        h = self._store[key]["value"]
        new_count = 0
        for i in range(0, len(args), 2):
            field = str(args[i])
            value = str(args[i + 1])
            if field not in h:
                new_count += 1
            h[field] = value
        return new_count

    def cmd_hget(self, key, field):
        ok, err = self._check_type(key, "hash", "HGET")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return "(nil)"
        h = entry["value"]
        field = str(field)
        if field not in h:
            return "(nil)"
        return h[field]

    def cmd_hdel(self, key, *fields):
        ok, err = self._check_type(key, "hash", "HDEL")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        h = entry["value"]
        removed = 0
        for f in fields:
            f = str(f)
            if f in h:
                del h[f]
                removed += 1
        return removed

    def cmd_hgetall(self, key):
        ok, err = self._check_type(key, "hash", "HGETALL")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return json.dumps({})
        return json.dumps(dict(entry["value"]))

    def cmd_hexists(self, key, field):
        ok, err = self._check_type(key, "hash", "HEXISTS")
        if not ok:
            return (False, err)
        entry = self._get_entry(key)
        if entry is None:
            return 0
        return 1 if str(field) in entry["value"] else 0

    # ------------------------------------------------------------------
    # Key Management
    # ------------------------------------------------------------------

    def cmd_keys(self, pattern=None):
        result = []
        for key in list(self._store.keys()):
            if self._is_expired(key):
                continue
            if pattern is None or fnmatch.fnmatch(key, pattern):
                result.append(key)
        return json.dumps(sorted(result))

    def cmd_type(self, key):
        return self._get_type(key)

    def cmd_expire(self, key, seconds):
        entry = self._get_entry(key)
        if entry is None:
            return 0
        try:
            seconds = int(seconds)
        except (ValueError, TypeError):
            return (False, "value is not an integer or out of range")
        entry["expires_at"] = self._now() + seconds
        return 1

    def cmd_ttl(self, key):
        entry = self._store.get(key)
        if entry is None:
            return -2
        if entry["expires_at"] is not None:
            remaining = int(entry["expires_at"] - self._now())
            if remaining <= 0:
                del self._store[key]
                return -2
            return remaining
        return -1

    # ------------------------------------------------------------------
    # Database Management
    # ------------------------------------------------------------------

    def cmd_flushdb(self):
        self._store.clear()
        return "OK"

    def cmd_dbsize(self):
        # Count live (non-expired) keys
        count = 0
        for key in list(self._store.keys()):
            if not self._is_expired(key):
                count += 1
        return count


# ------------------------------------------------------------------
# Command dispatch
# ------------------------------------------------------------------

def parse_line(line):
    """Parse a command line with shell-like whitespace splitting."""
    line = line.strip().lstrip("\ufeff")
    if not line or line.startswith("#"):
        return None
    parts = line.split()
    return parts


def run_command(db, args):
    """Execute a single command. Returns (output, is_error)."""
    cmd = args[0].upper()

    if cmd == "SET":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_set(args[1], args[2]), False

    elif cmd == "GET":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_get(args[1]), False

    elif cmd == "DEL":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_del(*args[1:]), False

    elif cmd == "EXISTS":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_exists(args[1]), False

    elif cmd == "LPUSH":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_lpush(args[1], *args[2:]), False

    elif cmd == "RPUSH":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_rpush(args[1], *args[2:]), False

    elif cmd == "LPOP":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_lpop(args[1]), False

    elif cmd == "RPOP":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_rpop(args[1]), False

    elif cmd == "LRANGE":
        if len(args) < 4:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_lrange(args[1], args[2], args[3]), False

    elif cmd == "LLEN":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_llen(args[1]), False

    elif cmd == "SADD":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_sadd(args[1], *args[2:]), False

    elif cmd == "SREM":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_srem(args[1], *args[2:]), False

    elif cmd == "SMEMBERS":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_smembers(args[1]), False

    elif cmd == "SISMEMBER":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_sismember(args[1], args[2]), False

    elif cmd == "SCARD":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_scard(args[1]), False

    elif cmd == "HSET":
        if len(args) < 4:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_hset(args[1], *args[2:]), False

    elif cmd == "HGET":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_hget(args[1], args[2]), False

    elif cmd == "HDEL":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_hdel(args[1], *args[2:]), False

    elif cmd == "HGETALL":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_hgetall(args[1]), False

    elif cmd == "HEXISTS":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_hexists(args[1], args[2]), False

    elif cmd == "KEYS":
        pattern = args[1] if len(args) > 1 else None
        return db.cmd_keys(pattern), False

    elif cmd == "TYPE":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_type(args[1]), False

    elif cmd == "EXPIRE":
        if len(args) < 3:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_expire(args[1], args[2]), False

    elif cmd == "TTL":
        if len(args) < 2:
            return (f"wrong number of arguments for '{cmd}' command", True)
        return db.cmd_ttl(args[1]), False

    elif cmd == "FLUSHDB":
        return db.cmd_flushdb(), False

    elif cmd == "DBSIZE":
        return db.cmd_dbsize(), False

    else:
        return (f"unknown command '{cmd}'", True)


def is_error(result):
    """Check if a command result is an error tuple."""
    if isinstance(result, tuple) and len(result) == 2 and result[0] is False:
        return True
    return False


def format_output(result):
    """Format result for stdout output."""
    if result is None:
        return ""
    if isinstance(result, bool):
        return ""
    return str(result)


def main():
    if len(sys.argv) < 2:
        print("Usage: miniredis.py COMMAND [ARGS...]  OR  miniredis.py --batch < commands.txt", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--batch":
        # Batch mode: read commands from stdin
        db = MiniRedisDB()
        exit_code = 0
        for line in sys.stdin:
            parts = parse_line(line)
            if parts is None:
                continue
            result, err_flag = run_command(db, parts)
            if is_error(result) or result is False:
                print(f"ERR {result[1] if isinstance(result, tuple) else result}", file=sys.stderr)
                exit_code = 1
                continue
            if err_flag:
                print(f"ERR {result}", file=sys.stderr)
                exit_code = 1
                continue
            output = format_output(result)
            if output:
                print(output)
        sys.exit(exit_code)
    else:
        # One-shot mode
        db = MiniRedisDB()
        result, err_flag = run_command(db, sys.argv[1:])
        if is_error(result) or result is False:
            msg = result[1] if isinstance(result, tuple) else result
            print(f"ERR {msg}", file=sys.stderr)
            sys.exit(1)
        if err_flag:
            print(f"ERR {result}", file=sys.stderr)
            sys.exit(1)
        output = format_output(result)
        if output:
            print(output)


if __name__ == "__main__":
    main()
