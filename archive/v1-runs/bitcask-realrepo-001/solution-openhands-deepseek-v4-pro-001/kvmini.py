#!/usr/bin/env python3.11
"""kvmini — A compact disk-backed key/value store with append-only log segments.

Usage:
    py -3.11 kvmini.py DBDIR COMMAND [ARGS...]

Commands: put, update, get, mget, delete, keys, count, list, stats, compact
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# On-disk format
#
# Segment files are named ``seg_0000000001``, ``seg_0000000002``, etc.
# Each line is a compact JSON record:
#   {"op":"put","k":"...","v":"..."}
#   {"op":"del","k":"..."}
#
# The active (newest) segment is always the one with the highest sequence
# number.  On open we replay all segments in name order — within each
# segment records are already in append order — so the *last* record for a
# key wins (tombstone removes it).
# ---------------------------------------------------------------------------

_SEGMENT_RE = re.compile(r"^seg_\d{10}$")
_DEFAULT_THRESHOLD = 1 * 1024 * 1024  # 1 MiB


def _sorted_segments(dbdir: str) -> list[str]:
    """Return sorted list of segment *filenames* (not paths) in *dbdir*."""
    if not os.path.isdir(dbdir):
        return []
    segments = [n for n in os.listdir(dbdir) if _SEGMENT_RE.match(n)]
    segments.sort()
    return segments


def _new_segment_name(segments: list[str]) -> str:
    """Return the filename for the segment after the last in *segments*."""
    if not segments:
        return "seg_0000000001"
    last_num = int(segments[-1].split("_")[1])
    return f"seg_{last_num + 1:010d}"


# ---------------------------------------------------------------------------
# State replay
# ---------------------------------------------------------------------------

def _replay(dbdir: str) -> tuple[dict[str, str], int]:
    """Replay all segment files in order.

    Returns ``(state, record_count)`` where *state* maps each live key to
    its current value.
    """
    state: dict[str, str] = {}
    record_count = 0

    for name in _sorted_segments(dbdir):
        path = os.path.join(dbdir, name)
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip("\n")
                if not line:
                    continue
                record_count += 1
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip corrupt lines (should never happen)
                key: str = rec.get("k", "")
                if rec.get("op") == "del":
                    state.pop(key, None)
                else:  # "put"
                    state[key] = rec.get("v", "")
    return state, record_count


# ---------------------------------------------------------------------------
# Append a single record
# ---------------------------------------------------------------------------

def _append(dbdir: str, op: str, key: str, value: str = "") -> None:
    """Append one record to the active segment, rolling over if needed."""
    os.makedirs(dbdir, exist_ok=True)

    if op == "put":
        rec = {"op": "put", "k": key, "v": value}
    else:
        rec = {"op": "del", "k": key}

    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n"

    # Determine rollover threshold
    threshold = _DEFAULT_THRESHOLD
    env_val = os.environ.get("KVMINI_MAX_SEGMENT_BYTES", "")
    if env_val:
        try:
            threshold = int(env_val)
        except ValueError:
            pass

    segments = _sorted_segments(dbdir)
    if segments:
        active = os.path.join(dbdir, segments[-1])
        if os.path.getsize(active) >= threshold:
            active = os.path.join(dbdir, _new_segment_name(segments))
    else:
        active = os.path.join(dbdir, "seg_0000000001")

    with open(active, "a", encoding="utf-8") as fh:
        fh.write(line)


# ---------------------------------------------------------------------------
# Compaction
# ---------------------------------------------------------------------------

def _compact(dbdir: str) -> None:
    """Rewrite the log so that only one record per live key remains.

    All tombstones and superseded records are permanently discarded.
    """
    state, _ = _replay(dbdir)

    # Remove every existing segment
    for name in _sorted_segments(dbdir):
        os.remove(os.path.join(dbdir, name))

    if not state:
        return  # nothing to write — next append will create seg_0000000001

    os.makedirs(dbdir, exist_ok=True)
    path = os.path.join(dbdir, "seg_0000000001")
    with open(path, "w", encoding="utf-8") as fh:
        for key in sorted(state):
            rec = {"op": "put", "k": key, "v": state[key]}
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_put(dbdir: str, args: list[str]) -> None:
    if len(args) != 2:
        _err("usage: kvmini.py DBDIR put KEY VALUE")
        sys.exit(1)
    _append(dbdir, "put", args[0], args[1])
    print("OK")


def cmd_update(dbdir: str, args: list[str]) -> None:
    if len(args) != 2:
        _err("usage: kvmini.py DBDIR update KEY VALUE")
        sys.exit(1)
    key, value = args
    state, _ = _replay(dbdir)
    if key not in state:
        _err(f"error: key '{key}' does not exist")
        sys.exit(1)
    _append(dbdir, "put", key, value)
    print("OK")


def cmd_get(dbdir: str, args: list[str]) -> None:
    if len(args) != 1:
        _err("usage: kvmini.py DBDIR get KEY")
        sys.exit(1)
    key = args[0]
    state, _ = _replay(dbdir)
    if key not in state:
        _err(f"error: key '{key}' does not exist")
        sys.exit(1)
    print(state[key])


def cmd_mget(dbdir: str, args: list[str]) -> None:
    if not args:
        _err("usage: kvmini.py DBDIR mget KEY [KEY...]")
        sys.exit(1)
    state, _ = _replay(dbdir)
    result = {k: state[k] for k in args if k in state}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def cmd_delete(dbdir: str, args: list[str]) -> None:
    if len(args) != 1:
        _err("usage: kvmini.py DBDIR delete KEY")
        sys.exit(1)
    key = args[0]
    state, _ = _replay(dbdir)
    if key not in state:
        _err(f"error: key '{key}' does not exist")
        sys.exit(1)
    _append(dbdir, "del", key)
    print("OK")


def cmd_keys(dbdir: str, args: list[str]) -> None:
    if args:
        _err("usage: kvmini.py DBDIR keys")
        sys.exit(1)
    state, _ = _replay(dbdir)
    print(json.dumps(sorted(state), ensure_ascii=False, separators=(",", ":")))


def cmd_count(dbdir: str, args: list[str]) -> None:
    if args:
        _err("usage: kvmini.py DBDIR count")
        sys.exit(1)
    state, _ = _replay(dbdir)
    print(len(state))


def cmd_list(dbdir: str, args: list[str]) -> None:
    if args:
        _err("usage: kvmini.py DBDIR list")
        sys.exit(1)
    state, _ = _replay(dbdir)
    result = {k: state[k] for k in sorted(state)}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def cmd_stats(dbdir: str, args: list[str]) -> None:
    if args:
        _err("usage: kvmini.py DBDIR stats")
        sys.exit(1)
    state, record_count = _replay(dbdir)
    print(
        json.dumps(
            {"live_keys": len(state), "log_entries": record_count},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def cmd_compact(dbdir: str, args: list[str]) -> None:
    if args:
        _err("usage: kvmini.py DBDIR compact")
        sys.exit(1)
    _compact(dbdir)
    print("OK")


_COMMANDS = {
    "put": cmd_put,
    "update": cmd_update,
    "get": cmd_get,
    "mget": cmd_mget,
    "delete": cmd_delete,
    "keys": cmd_keys,
    "count": cmd_count,
    "list": cmd_list,
    "stats": cmd_stats,
    "compact": cmd_compact,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 3:
        _err(f"usage: {sys.argv[0]} DBDIR COMMAND [ARGS...]")
        sys.exit(1)

    dbdir = sys.argv[1]
    cmd = sys.argv[2]
    args = sys.argv[3:]

    handler = _COMMANDS.get(cmd)
    if handler is None:
        _err(f"error: unknown command '{cmd}'")
        sys.exit(1)

    handler(dbdir, args)


if __name__ == "__main__":
    main()
