import time
import pickle

class CommandError(Exception):
    """Raised when an operation is performed on a key with the wrong type."""
    pass

class QueueServer:
    """In-memory data structure store with type enforcement and optional persistence."""

    def __init__(self, use_gevent=False):
        # use_gevent is ignored in this implementation
        self._data = {}          # key -> {'value': obj, 'type': str, 'expiry': float|None}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _check_expired(self, key):
        """If key exists and is expired, delete it and return False. Otherwise return True if key exists, False if missing."""
        if key in self._data:
            expiry = self._data[key].get('expiry')
            if expiry is not None and time.time() > expiry:
                del self._data[key]
                return False
            return True
        return False

    def _ensure_type(self, key, expected_type, create=False):
        """
        Check that `key` exists and is of `expected_type`.
        If `create` is True and key missing, create an empty container of the correct type.
        Returns the value (container) or None if key missing and not creating.
        Raises CommandError on type mismatch.
        """
        self._check_expired(key)
        if key in self._data:
            if self._data[key]['type'] != expected_type:
                raise CommandError(f"Key '{key}' is not a {expected_type}")
            return self._data[key]['value']
        else:
            if create:
                if expected_type == 'QUEUE':
                    value = []
                elif expected_type == 'SET':
                    value = set()
                elif expected_type == 'HASH':
                    value = {}
                else:
                    value = None
                self._data[key] = {'value': value, 'type': expected_type, 'expiry': None}
                return value
            return None

    # ------------------------------------------------------------------
    # String operations
    # ------------------------------------------------------------------
    def kv_set(self, key, value):
        """Store a value, auto-detecting type: dict->HASH, list->QUEUE, set->SET, other->KV (string)."""
        if isinstance(value, dict):
            typ = 'HASH'
        elif isinstance(value, list):
            typ = 'QUEUE'
        elif isinstance(value, set):
            typ = 'SET'
        else:
            typ = 'KV'
        self._data[key] = {'value': value, 'type': typ, 'expiry': None}
        return 1

    def kv_get(self, key):
        """Return the value or None if the key does not exist or has expired."""
        if self._check_expired(key):
            return self._data[key]['value']
        return None

    def kv_delete(self, key):
        """Remove the key. Returns 1 if deleted, 0 if not found."""
        self._check_expired(key)
        if key in self._data:
            del self._data[key]
            return 1
        return 0

    def kv_exists(self, key):
        """Return 1 if key exists and is not expired, 0 otherwise."""
        self._check_expired(key)
        return 1 if key in self._data else 0

    def kv_incr(self, key):
        """Increment a numeric value by 1. Creates at 0 if missing. Raises CommandError on non-numeric."""
        if not self._check_expired(key):
            self._data[key] = {'value': 0, 'type': 'KV', 'expiry': None}
        else:
            entry = self._data[key]
            if entry['type'] != 'KV':
                raise CommandError(f"Key '{key}' is not a KV")
            if not isinstance(entry['value'], (int, float)):
                raise CommandError(f"Value at key '{key}' is not numeric")
        self._data[key]['value'] += 1
        return self._data[key]['value']

    def kv_decr(self, key):
        """Decrement a numeric value by 1. Creates at 0 if missing. Raises CommandError on non-numeric."""
        if not self._check_expired(key):
            self._data[key] = {'value': 0, 'type': 'KV', 'expiry': None}
        else:
            entry = self._data[key]
            if entry['type'] != 'KV':
                raise CommandError(f"Key '{key}' is not a KV")
            if not isinstance(entry['value'], (int, float)):
                raise CommandError(f"Value at key '{key}' is not numeric")
        self._data[key]['value'] -= 1
        return self._data[key]['value']

    # ------------------------------------------------------------------
    # Bulk string operations
    # ------------------------------------------------------------------
    def kv_mset(self, __data=None, **kwargs):
        """Set multiple string keys from a dict and/or keyword arguments. Returns count of keys set."""
        data = {}
        if __data is not None:
            data.update(__data)
        data.update(kwargs)
        for k, v in data.items():
            # Always store as KV (string) regardless of the value's Python type
            self._data[k] = {'value': v, 'type': 'KV', 'expiry': None}
        return len(data)

    def kv_mget(self, *keys):
        """Return a list of values for the given keys. Missing keys appear as None."""
        result = []
        for k in keys:
            if self._check_expired(k):
                result.append(self._data[k]['value'])
            else:
                result.append(None)
        return result

    # ------------------------------------------------------------------
    # List operations
    # ------------------------------------------------------------------
    def lpush(self, key, *values):
        """Prepend values to the head of the list. Creates the list if missing. Returns number pushed."""
        lst = self._ensure_type(key, 'QUEUE', create=True)
        for v in values:
            lst.insert(0, v)
        return len(values)

    def rpush(self, key, *values):
        """Append values to the tail of the list. Creates the list if missing. Returns number pushed."""
        lst = self._ensure_type(key, 'QUEUE', create=True)
        lst.extend(values)
        return len(values)

    def lpop(self, key):
        """Remove and return the first element, or None if empty/missing."""
        if self._check_expired(key) and key in self._data:
            if self._data[key]['type'] != 'QUEUE':
                raise CommandError(f"Key '{key}' is not a QUEUE")
            lst = self._data[key]['value']
            if lst:
                return lst.pop(0)
        return None

    def rpop(self, key):
        """Remove and return the last element, or None if empty/missing."""
        if self._check_expired(key) and key in self._data:
            if self._data[key]['type'] != 'QUEUE':
                raise CommandError(f"Key '{key}' is not a QUEUE")
            lst = self._data[key]['value']
            if lst:
                return lst.pop()
        return None

    def lrange(self, key, start, end=None):
        """Return a slice of the list. Raises CommandError on non-list keys."""
        if not self._check_expired(key) or key not in self._data:
            raise CommandError(f"Key '{key}' does not exist or is not a QUEUE")
        if self._data[key]['type'] != 'QUEUE':
            raise CommandError(f"Key '{key}' is not a QUEUE")
        lst = self._data[key]['value']
        if end is None:
            return lst[start:]
        return lst[start:end]

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------
    def sadd(self, key, *members):
        """Add members to a set. Creates it if missing. Returns new cardinality."""
        s = self._ensure_type(key, 'SET', create=True)
        s.update(members)
        return len(s)

    def srem(self, key, *members):
        """Remove members from a set. Returns number of members actually removed."""
        if not self._check_expired(key) or key not in self._data:
            return 0
        if self._data[key]['type'] != 'SET':
            raise CommandError(f"Key '{key}' is not a SET")
        s = self._data[key]['value']
        removed = 0
        for m in members:
            if m in s:
                s.remove(m)
                removed += 1
        return removed

    def smembers(self, key):
        """Return the internal set object. Creates an empty set if missing. Raises CommandError on non-set keys."""
        s = self._ensure_type(key, 'SET', create=True)
        return s

    def scard(self, key):
        """Return set cardinality. Creates empty set if missing and returns 0. Raises CommandError on non-set keys."""
        s = self._ensure_type(key, 'SET', create=True)
        return len(s)

    # ------------------------------------------------------------------
    # Hash operations
    # ------------------------------------------------------------------
    def hset(self, key, field, value):
        """Set a field in the hash. Creates the hash if missing. Returns 1."""
        h = self._ensure_type(key, 'HASH', create=True)
        h[field] = value
        return 1

    def hget(self, key, field):
        """Return the value of a field, or None if missing. Raises CommandError on non-hash keys."""
        if not self._check_expired(key) or key not in self._data:
            return None
        if self._data[key]['type'] != 'HASH':
            raise CommandError(f"Key '{key}' is not a HASH")
        return self._data[key]['value'].get(field, None)

    def hdel(self, key, field):
        """Delete a field from the hash. Returns 1 if deleted, 0 if not found. Raises CommandError on non-hash keys."""
        if not self._check_expired(key) or key not in self._data:
            return 0
        if self._data[key]['type'] != 'HASH':
            raise CommandError(f"Key '{key}' is not a HASH")
        h = self._data[key]['value']
        if field in h:
            del h[field]
            return 1
        return 0

    def hgetall(self, key):
        """Return the internal hash dict. Creates empty hash if missing. Raises CommandError on non-hash keys."""
        h = self._ensure_type(key, 'HASH', create=True)
        return h

    # ------------------------------------------------------------------
    # Key management & persistence
    # ------------------------------------------------------------------
    def expire(self, key, nseconds):
        """Set a timeout in seconds on a key. Returns None. No-op if key missing."""
        if key in self._data:
            self._data[key]['expiry'] = time.time() + nseconds

    def kv_flush(self):
        """Remove all keys. Returns number of keys removed before flush."""
        count = len(self._data)
        self._data.clear()
        return count

    def save_to_disk(self, filename):
        """Persist the entire database state to a file using pickle. Returns True."""
        with open(filename, 'wb') as f:
            pickle.dump(self._data, f)
        return True

    def restore_from_disk(self, filename):
        """Restore database state from a pickle file. Returns True if restored, False if file does not exist."""
        try:
            with open(filename, 'rb') as f:
                self._data = pickle.load(f)
            return True
        except FileNotFoundError:
            return False
