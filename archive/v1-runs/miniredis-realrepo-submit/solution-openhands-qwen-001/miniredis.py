#!/usr/bin/env python3
"""
MiniRedis - A compact in-memory data structure store.

Supports string keys, lists, sets, hashes, key expiry, pattern-based key
enumeration, and type-aware error handling.

Usage:
    py -3.11 miniredis.py COMMAND [ARGS...]
    py -3.11 miniredis.py --batch < commands.txt
"""

import json
import sys
import time
import fnmatch
from typing import Any


class MiniRedis:
    """In-memory data structure store with Redis-like semantics."""

    def __init__(self):
        # keys: dict mapping key_name -> {'type': str, 'value': Any, 'expiry': float | None}
        self._keys: dict[str, dict[str, Any]] = {}

    def _is_expired(self, key_name: str) -> bool:
        """Check if a key has expired."""
        if key_name not in self._keys:
            return True
        entry = self._keys[key_name]
        if entry['expiry'] is not None and time.time() > entry['expiry']:
            return True
        return False

    def _get_live_entry(self, key_name: str) -> dict[str, Any] | None:
        """Get a key's entry if it exists and is not expired."""
        if key_name not in self._keys:
            return None
        if self._is_expired(key_name):
            return None
        return self._keys[key_name]

    def _delete_key(self, key_name: str) -> bool:
        """Delete a key. Returns True if key existed."""
        if key_name in self._keys:
            del self._keys[key_name]
            return True
        return False

    # String operations
    def set_key(self, key_name: str, value: str) -> str:
        """Set a string key, overwriting any previous value/type/expiry."""
        self._keys[key_name] = {
            'type': 'string',
            'value': value,
            'expiry': None
        }
        return "OK"

    def get_key(self, key_name: str) -> str | None:
        """Get the value of a string key."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return None
        if entry['type'] != 'string':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        return entry['value']

    def exists(self, key_name: str) -> int:
        """Check if a key exists (any type, not expired)."""
        return 1 if self._get_live_entry(key_name) is not None else 0

    def delete_keys(self, key_names: list[str]) -> int:
        """Delete one or more keys. Return count of keys actually removed."""
        count = 0
        for key_name in key_names:
            if self._delete_key(key_name):
                count += 1
        return count

    # List operations
    def lpush(self, key_name: str, elements: list[str]) -> int:
        """Prepend elements to a list. Creates list if key doesn't exist."""
        entry = self._get_live_entry(key_name)
        if entry is not None and entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if entry is None:
            self._keys[key_name] = {
                'type': 'list',
                'value': [],
                'expiry': None
            }
            entry = self._keys[key_name]
        
        # Prepend elements (in order given, so last element ends up first)
        for elem in reversed(elements):
            entry['value'].insert(0, elem)
        
        return len(entry['value'])

    def rpush(self, key_name: str, elements: list[str]) -> int:
        """Append elements to a list. Creates list if key doesn't exist."""
        entry = self._get_live_entry(key_name)
        if entry is not None and entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if entry is None:
            self._keys[key_name] = {
                'type': 'list',
                'value': [],
                'expiry': None
            }
            entry = self._keys[key_name]
        
        entry['value'].extend(elements)
        return len(entry['value'])

    def lpop(self, key_name: str) -> str | None:
        """Remove and return the first element of a list."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return None
        if entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if len(entry['value']) == 0:
            return None
        
        return entry['value'].pop(0)

    def rpop(self, key_name: str) -> str | None:
        """Remove and return the last element of a list."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return None
        if entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if len(entry['value']) == 0:
            return None
        
        return entry['value'].pop()

    def lrange(self, key_name: str, start: int, stop: int) -> list[str]:
        """Return a slice of the list."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return []
        if entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        lst = entry['value']
        # Normalize negative indices
        if start < 0:
            start = max(0, len(lst) + start)
        if stop < 0:
            stop = max(0, len(lst) + stop)
        
        # Python slice is exclusive of stop, but LRANGE is inclusive
        result = lst[start:stop+1] if start <= len(lst) else []
        return result

    def llen(self, key_name: str) -> int:
        """Return the length of a list."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'list':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return len(entry['value'])

    # Set operations
    def sadd(self, key_name: str, members: list[str]) -> int:
        """Add members to a set. Creates set if key doesn't exist."""
        entry = self._get_live_entry(key_name)
        if entry is not None and entry['type'] != 'set':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if entry is None:
            self._keys[key_name] = {
                'type': 'set',
                'value': set(),
                'expiry': None
            }
            entry = self._keys[key_name]
        
        before_size = len(entry['value'])
        for member in members:
            entry['value'].add(member)
        
        return len(entry['value']) - before_size

    def srem(self, key_name: str, members: list[str]) -> int:
        """Remove members from a set."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'set':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        before_size = len(entry['value'])
        for member in members:
            entry['value'].discard(member)
        
        return before_size - len(entry['value'])

    def smembers(self, key_name: str) -> list[str]:
        """Return all members of a set."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return []
        if entry['type'] != 'set':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return sorted(list(entry['value']))

    def sismember(self, key_name: str, member: str) -> int:
        """Check if a member is in the set."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'set':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return 1 if member in entry['value'] else 0

    def scard(self, key_name: str) -> int:
        """Return the number of members in the set."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'set':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return len(entry['value'])

    # Hash operations
    def hset(self, key_name: str, field_value_pairs: list[tuple[str, str]]) -> int:
        """Set field-value pairs in a hash. Returns count of new fields."""
        entry = self._get_live_entry(key_name)
        if entry is not None and entry['type'] != 'hash':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if entry is None:
            self._keys[key_name] = {
                'type': 'hash',
                'value': {},
                'expiry': None
            }
            entry = self._keys[key_name]
        
        new_count = 0
        for field, value in field_value_pairs:
            if field not in entry['value']:
                new_count += 1
            entry['value'][field] = value
        
        return new_count

    def hget(self, key_name: str, field: str) -> str | None:
        """Get the value of a field in a hash."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return None
        if entry['type'] != 'hash':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return entry['value'].get(field)

    def hdel(self, key_name: str, fields: list[str]) -> int:
        """Delete fields from a hash."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'hash':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        count = 0
        for field in fields:
            if field in entry['value']:
                del entry['value'][field]
                count += 1
        
        return count

    def hgetall(self, key_name: str) -> dict[str, str]:
        """Get all field-value pairs from a hash."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return {}
        if entry['type'] != 'hash':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return dict(entry['value'])

    def hexists(self, key_name: str, field: str) -> int:
        """Check if a field exists in a hash."""
        entry = self._get_live_entry(key_name)
        if entry is None:
            return 0
        if entry['type'] != 'hash':
            raise TypeError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return 1 if field in entry['value'] else 0

    # Key management
    def keys(self, pattern: str = '*') -> list[str]:
        """Return matching keys (excluding expired)."""
        live_keys = [k for k in self._keys.keys() if not self._is_expired(k)]
        return sorted(fnmatch.filter(live_keys, pattern))

    def type_of(self, key_name: str) -> str:
        """Return the type of a key."""
        if self._is_expired(key_name):
            return "none"
        if key_name not in self._keys:
            return "none"
        return self._keys[key_name]['type']

    def expire(self, key_name: str, seconds: int) -> int:
        """Set a timeout on a key."""
        if self._is_expired(key_name) and key_name not in self._keys:
            return 0
        
        entry = self._keys.get(key_name)
        if entry is None:
            return 0
        
        if seconds <= 0:
            # Immediate expiry
            entry['expiry'] = time.time()
        else:
            entry['expiry'] = time.time() + seconds
        
        # Check if entry is now expired (for <= 0 case)
        if self._is_expired(key_name):
            return 0
        
        return 1

    def ttl(self, key_name: str) -> int:
        """Return the remaining time to live in seconds."""
        if key_name not in self._keys:
            return -2
        
        entry = self._keys[key_name]
        if self._is_expired(key_name):
            return -2
        
        if entry['expiry'] is None:
            return -1
        
        remaining = int(entry['expiry'] - time.time())
        return max(remaining, -2)

    # Database management
    def flushdb(self) -> str:
        """Remove all keys from the database."""
        self._keys.clear()
        return "OK"

    def dbsize(self) -> int:
        """Return the number of live (non-expired) keys."""
        return sum(1 for k in self._keys.keys() if not self._is_expired(k))


def parse_args(args: list[str]) -> tuple[str, list[str]]:
    """Parse command-line arguments handling quoted strings."""
    result = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('"') or arg.startswith("'"):
            # This is a quoted argument, need to handle it
            quote_char = arg[0]
            # Check if it's a complete quoted string
            if arg.endswith(quote_char) and len(arg) > 1:
                result.append(arg[1:-1])
            else:
                # Need to collect more arguments until we find the closing quote
                parts = [arg]
                while i + 1 < len(args):
                    i += 1
                    parts.append(args[i])
                    if args[i].endswith(quote_char):
                        break
                result.append(' '.join(parts))
        else:
            result.append(arg)
        i += 1
    
    if not result:
        return '', []
    
    return result[0], result[1:]


def execute_command(db: MiniRedis, command: str, args: list[str]) -> Any:
    """Execute a single command. Returns result or raises exception."""
    command = command.upper()
    
    if command == 'SET':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'SET' command")
        return db.set_key(args[0], args[1])
    
    elif command == 'GET':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'GET' command")
        result = db.get_key(args[0])
        return result if result is not None else "(nil)"
    
    elif command == 'DEL':
        if len(args) < 1:
            raise ValueError("ERR wrong number of arguments for 'DEL' command")
        return db.delete_keys(args)
    
    elif command == 'EXISTS':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'EXISTS' command")
        return db.exists(args[0])
    
    elif command == 'LPUSH':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'LPUSH' command")
        return db.lpush(args[0], args[1:])
    
    elif command == 'RPUSH':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'RPUSH' command")
        return db.rpush(args[0], args[1:])
    
    elif command == 'LPOP':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'LPOP' command")
        result = db.lpop(args[0])
        return result if result is not None else "(nil)"
    
    elif command == 'RPOP':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'RPOP' command")
        result = db.rpop(args[0])
        return result if result is not None else "(nil)"
    
    elif command == 'LRANGE':
        if len(args) != 3:
            raise ValueError("ERR wrong number of arguments for 'LRANGE' command")
        try:
            start = int(args[1])
            stop = int(args[2])
        except ValueError:
            raise ValueError("ERR value is not an integer or out of range")
        result = db.lrange(args[0], start, stop)
        return json.dumps(result)
    
    elif command == 'LLEN':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'LLEN' command")
        return db.llen(args[0])
    
    elif command == 'SADD':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'SADD' command")
        return db.sadd(args[0], args[1:])
    
    elif command == 'SREM':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'SREM' command")
        return db.srem(args[0], args[1:])
    
    elif command == 'SMEMBERS':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'SMEMBERS' command")
        result = db.smembers(args[0])
        return json.dumps(result)
    
    elif command == 'SISMEMBER':
        if len(args) != 2:
            raise ValueError("ERR wrong number of arguments for 'SISMEMBER' command")
        return db.sismember(args[0], args[1])
    
    elif command == 'SCARD':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'SCARD' command")
        return db.scard(args[0])
    
    elif command == 'HSET':
        if len(args) < 3 or len(args) % 2 == 0:
            raise ValueError("ERR wrong number of arguments for 'HSET' command")
        field_value_pairs = []
        for i in range(1, len(args), 2):
            field_value_pairs.append((args[i], args[i+1]))
        return db.hset(args[0], field_value_pairs)
    
    elif command == 'HGET':
        if len(args) != 2:
            raise ValueError("ERR wrong number of arguments for 'HGET' command")
        result = db.hget(args[0], args[1])
        return result if result is not None else "(nil)"
    
    elif command == 'HDEL':
        if len(args) < 2:
            raise ValueError("ERR wrong number of arguments for 'HDEL' command")
        return db.hdel(args[0], args[1:])
    
    elif command == 'HGETALL':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'HGETALL' command")
        result = db.hgetall(args[0])
        return json.dumps(result)
    
    elif command == 'HEXISTS':
        if len(args) != 2:
            raise ValueError("ERR wrong number of arguments for 'HEXISTS' command")
        return db.hexists(args[0], args[1])
    
    elif command == 'KEYS':
        if len(args) == 0:
            pattern = '*'
        elif len(args) == 1:
            pattern = args[0]
        else:
            raise ValueError("ERR wrong number of arguments for 'KEYS' command")
        result = db.keys(pattern)
        return json.dumps(result)
    
    elif command == 'TYPE':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'TYPE' command")
        return db.type_of(args[0])
    
    elif command == 'EXPIRE':
        if len(args) != 2:
            raise ValueError("ERR wrong number of arguments for 'EXPIRE' command")
        try:
            seconds = int(args[1])
        except ValueError:
            raise ValueError("ERR value is not an integer or out of range")
        return db.expire(args[0], seconds)
    
    elif command == 'TTL':
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'TTL' command")
        return db.ttl(args[0])
    
    elif command == 'FLUSHDB':
        if len(args) != 0:
            raise ValueError("ERR wrong number of arguments for 'FLUSHDB' command")
        return db.flushdb()
    
    elif command == 'DBSIZE':
        if len(args) != 0:
            raise ValueError("ERR wrong number of arguments for 'DBSIZE' command")
        return db.dbsize()
    
    else:
        raise ValueError(f"ERR unknown command '{command}'")


def main():
    if len(sys.argv) < 2:
        print("Usage: miniredis.py COMMAND [ARGS...]", file=sys.stderr)
        print("       miniredis.py --batch < commands.txt", file=sys.stderr)
        sys.exit(1)
    
    db = MiniRedis()
    
    if sys.argv[1] == '--batch':
        # Batch mode: read commands from stdin
        lines = sys.stdin.read().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse the line as shell-like arguments
            parts = line.split()
            if not parts:
                continue
            
            command = parts[0]
            args = parts[1:]
            
            try:
                result = execute_command(db, command, args)
                print(result)
            except TypeError as e:
                print(str(e), file=sys.stderr)
            except ValueError as e:
                print(str(e), file=sys.stderr)
            except Exception as e:
                print(f"ERR {str(e)}", file=sys.stderr)
    else:
        # One-shot mode
        command = sys.argv[1]
        args = sys.argv[2:]
        
        try:
            result = execute_command(db, command, args)
            print(result)
        except TypeError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERR {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()