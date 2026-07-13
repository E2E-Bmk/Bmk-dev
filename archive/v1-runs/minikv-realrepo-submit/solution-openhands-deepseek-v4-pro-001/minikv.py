import pickle
import time


class CommandError(Exception):
    """Raised for type mismatches or invalid operations."""
    pass


class QueueServer:
    def __init__(self, use_gevent=False):
        self._store = {}       # key -> [value, type_label, expiry_time]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_type(value):
        if isinstance(value, dict):
            return 'hash'
        if isinstance(value, list):
            return 'queue'
        if isinstance(value, set):
            return 'set'
        return 'kv'

    def _check_expiry(self, key):
        if key in self._store:
            _, _, expiry = self._store[key]
            if expiry is not None and time.time() > expiry:
                del self._store[key]
                return False
        return key in self._store

    # ------------------------------------------------------------------
    # String key-value operations
    # ------------------------------------------------------------------

    def kv_set(self, key, value):
        t = self._detect_type(value)
        self._store[key] = [value, t, None]
        return 1

    def kv_get(self, key):
        if not self._check_expiry(key):
            return None
        return self._store[key][0]

    def kv_delete(self, key):
        if key in self._store:
            self._check_expiry(key)
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    def kv_exists(self, key):
        return 1 if self._check_expiry(key) else 0

    def kv_incr(self, key):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [0, 'kv', None]
            return 0
        current = self._store[key]
        if current[1] != 'kv':
            raise CommandError(
                f"kv_incr on key '{key}' of type '{current[1]}' not permitted"
            )
        val = current[0]
        if isinstance(val, str):
            raise CommandError(
                f"kv_incr requires numeric value, got string"
            )
        if not isinstance(val, (int, float)):
            raise CommandError(
                f"kv_incr requires numeric value"
            )
        current[0] = val + 1
        return current[0]

    def kv_decr(self, key):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [0, 'kv', None]
            return 0
        current = self._store[key]
        if current[1] != 'kv':
            raise CommandError(
                f"kv_decr on key '{key}' of type '{current[1]}' not permitted"
            )
        val = current[0]
        if isinstance(val, str):
            raise CommandError(
                f"kv_decr requires numeric value, got string"
            )
        if not isinstance(val, (int, float)):
            raise CommandError(
                f"kv_decr requires numeric value"
            )
        current[0] = val - 1
        return current[0]

    # ------------------------------------------------------------------
    # Bulk string operations
    # ------------------------------------------------------------------

    def kv_mset(self, __data=None, **kwargs):
        data = {}
        if __data is not None:
            data.update(__data)
        data.update(kwargs)
        count = 0
        for k, v in data.items():
            self.kv_set(k, v)
            count += 1
        return count

    def kv_mget(self, *keys):
        return [self.kv_get(k) for k in keys]

    # ------------------------------------------------------------------
    # List operations
    # ------------------------------------------------------------------

    def lpush(self, key, *values):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [[], 'queue', None]
        else:
            current = self._store[key]
            if current[1] != 'queue':
                raise CommandError(
                    f"lpush on key '{key}' of type '{current[1]}' not permitted"
                )
        lst = self._store[key][0]
        for v in values:
            lst.insert(0, v)
        return len(values)

    def rpush(self, key, *values):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [[], 'queue', None]
        else:
            current = self._store[key]
            if current[1] != 'queue':
                raise CommandError(
                    f"rpush on key '{key}' of type '{current[1]}' not permitted"
                )
        lst = self._store[key][0]
        lst.extend(values)
        return len(values)

    def lpop(self, key):
        self._check_expiry(key)
        if key not in self._store:
            return None
        current = self._store[key]
        if current[1] != 'queue':
            raise CommandError(
                f"lpop on key '{key}' of type '{current[1]}' not permitted"
            )
        lst = current[0]
        if not lst:
            return None
        return lst.pop(0)

    def rpop(self, key):
        self._check_expiry(key)
        if key not in self._store:
            return None
        current = self._store[key]
        if current[1] != 'queue':
            raise CommandError(
                f"rpop on key '{key}' of type '{current[1]}' not permitted"
            )
        lst = current[0]
        if not lst:
            return None
        return lst.pop()

    def lrange(self, key, start, end=None):
        self._check_expiry(key)
        if key not in self._store:
            raise CommandError(
                f"lrange on non-existent key '{key}'"
            )
        current = self._store[key]
        if current[1] != 'queue':
            raise CommandError(
                f"lrange on key '{key}' of type '{current[1]}' not permitted"
            )
        lst = current[0]
        if end is None:
            return lst[start:]
        return lst[start:end]

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def sadd(self, key, *members):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [set(), 'set', None]
        elif self._store[key][1] != 'set':
            raise CommandError(
                f"sadd on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        s = self._store[key][0]
        for m in members:
            s.add(m)
        return len(s)

    def srem(self, key, *members):
        self._check_expiry(key)
        if key not in self._store:
            return 0
        if self._store[key][1] != 'set':
            raise CommandError(
                f"srem on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        s = self._store[key][0]
        count = 0
        for m in members:
            if m in s:
                s.remove(m)
                count += 1
        return count

    def smembers(self, key):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [set(), 'set', None]
        elif self._store[key][1] != 'set':
            raise CommandError(
                f"smembers on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        return self._store[key][0]

    def scard(self, key):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [set(), 'set', None]
            return 0
        if self._store[key][1] != 'set':
            raise CommandError(
                f"scard on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        return len(self._store[key][0])

    # ------------------------------------------------------------------
    # Hash operations
    # ------------------------------------------------------------------

    def hset(self, key, field, value):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [{}, 'hash', None]
        elif self._store[key][1] != 'hash':
            raise CommandError(
                f"hset on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        self._store[key][0][field] = value
        return 1

    def hget(self, key, field):
        self._check_expiry(key)
        if key not in self._store:
            return None
        if self._store[key][1] != 'hash':
            raise CommandError(
                f"hget on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        return self._store[key][0].get(field, None)

    def hdel(self, key, field):
        self._check_expiry(key)
        if key not in self._store:
            return 0
        if self._store[key][1] != 'hash':
            raise CommandError(
                f"hdel on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        d = self._store[key][0]
        if field in d:
            del d[field]
            return 1
        return 0

    def hgetall(self, key):
        self._check_expiry(key)
        if key not in self._store:
            self._store[key] = [{}, 'hash', None]
        elif self._store[key][1] != 'hash':
            raise CommandError(
                f"hgetall on key '{key}' of type '{self._store[key][1]}' not permitted"
            )
        return self._store[key][0]

    # ------------------------------------------------------------------
    # Key management and persistence
    # ------------------------------------------------------------------

    def expire(self, key, nseconds):
        if key in self._store:
            self._store[key][2] = time.time() + nseconds
        return None

    def kv_flush(self):
        count = len(self._store)
        self._store.clear()
        return count

    def save_to_disk(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self._store, f)
        return True

    def restore_from_disk(self, filename):
        import os
        if not os.path.exists(filename):
            return False
        with open(filename, 'rb') as f:
            self._store = pickle.load(f)
        return True
