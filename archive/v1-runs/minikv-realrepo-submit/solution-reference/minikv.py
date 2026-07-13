import os
import pickle
import time


class CommandError(Exception):
    pass


KV = "kv"
QUEUE = "queue"
SET = "set"
HASH = "hash"


class QueueServer:
    def __init__(self, use_gevent=False):
        self._values = {}
        self._types = {}
        self._expiry = {}

    def _purge_if_expired(self, key):
        deadline = self._expiry.get(key)
        if deadline is not None and time.time() >= deadline:
            self._values.pop(key, None)
            self._types.pop(key, None)
            self._expiry.pop(key, None)

    def _exists(self, key):
        self._purge_if_expired(key)
        return key in self._values

    def _type(self, key):
        self._purge_if_expired(key)
        return self._types.get(key)

    def _require_type(self, key, typ):
        actual = self._type(key)
        if actual is not None and actual != typ:
            raise CommandError(f"wrong type: expected {typ}, got {actual}")

    def kv_set(self, key, value):
        if isinstance(value, dict):
            typ = HASH
        elif isinstance(value, list):
            typ = QUEUE
        elif isinstance(value, set):
            typ = SET
        else:
            typ = KV
        self._values[key] = value
        self._types[key] = typ
        self._expiry.pop(key, None)
        return 1

    def kv_get(self, key):
        self._purge_if_expired(key)
        return self._values.get(key)

    def kv_delete(self, key):
        self._purge_if_expired(key)
        if key not in self._values:
            return 0
        self._values.pop(key, None)
        self._types.pop(key, None)
        self._expiry.pop(key, None)
        return 1

    def kv_exists(self, key):
        return 1 if self._exists(key) else 0

    def kv_incr(self, key):
        if not self._exists(key):
            self.kv_set(key, 0)
        self._require_type(key, KV)
        value = self._values[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise CommandError("value is not numeric")
        value += 1
        self._values[key] = value
        return value

    def kv_decr(self, key):
        if not self._exists(key):
            self.kv_set(key, 0)
        self._require_type(key, KV)
        value = self._values[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise CommandError("value is not numeric")
        value -= 1
        self._values[key] = value
        return value

    def kv_mset(self, __data=None, **kwargs):
        count = 0
        if __data:
            for key, value in __data.items():
                self.kv_set(key, value)
                count += 1
        for key, value in kwargs.items():
            self.kv_set(key, value)
            count += 1
        return count

    def kv_mget(self, *keys):
        return [self.kv_get(key) for key in keys]

    def lpush(self, key, *values):
        self._require_type(key, QUEUE)
        if not self._exists(key):
            self._values[key] = []
            self._types[key] = QUEUE
        for value in values:
            self._values[key].insert(0, value)
        return len(values)

    def rpush(self, key, *values):
        self._require_type(key, QUEUE)
        if not self._exists(key):
            self._values[key] = []
            self._types[key] = QUEUE
        self._values[key].extend(values)
        return len(values)

    def lpop(self, key):
        self._require_type(key, QUEUE)
        if not self._exists(key) or not self._values[key]:
            return None
        return self._values[key].pop(0)

    def rpop(self, key):
        self._require_type(key, QUEUE)
        if not self._exists(key) or not self._values[key]:
            return None
        return self._values[key].pop()

    def lrange(self, key, start, end=None):
        self._require_type(key, QUEUE)
        if not self._exists(key):
            return []
        return self._values[key][start:end]

    def sadd(self, key, *members):
        self._require_type(key, SET)
        if not self._exists(key):
            self._values[key] = set()
            self._types[key] = SET
        self._values[key].update(members)
        return len(self._values[key])

    def srem(self, key, *members):
        self._require_type(key, SET)
        if not self._exists(key):
            return 0
        removed = 0
        for member in members:
            if member in self._values[key]:
                self._values[key].remove(member)
                removed += 1
        return removed

    def smembers(self, key):
        self._require_type(key, SET)
        if not self._exists(key):
            self._values[key] = set()
            self._types[key] = SET
        return self._values[key]

    def scard(self, key):
        self._require_type(key, SET)
        if not self._exists(key):
            self._values[key] = set()
            self._types[key] = SET
        return len(self._values[key])

    def hset(self, key, field, value):
        self._require_type(key, HASH)
        if not self._exists(key):
            self._values[key] = {}
            self._types[key] = HASH
        self._values[key][field] = value
        return 1

    def hget(self, key, field):
        self._require_type(key, HASH)
        if not self._exists(key):
            return None
        return self._values[key].get(field)

    def hdel(self, key, field):
        self._require_type(key, HASH)
        if not self._exists(key) or field not in self._values[key]:
            return 0
        del self._values[key][field]
        return 1

    def hgetall(self, key):
        self._require_type(key, HASH)
        if not self._exists(key):
            self._values[key] = {}
            self._types[key] = HASH
        return self._values[key]

    def expire(self, key, nseconds):
        if self._exists(key):
            self._expiry[key] = time.time() + float(nseconds)
        return None

    def kv_flush(self):
        count = len([key for key in list(self._values) if self._exists(key)])
        self._values.clear()
        self._types.clear()
        self._expiry.clear()
        return count

    def save_to_disk(self, filename):
        data = {
            "values": self._values,
            "types": self._types,
            "expiry": self._expiry,
        }
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        return True

    def restore_from_disk(self, filename):
        if not os.path.exists(filename):
            return False
        with open(filename, "rb") as f:
            data = pickle.load(f)
        self._values = data.get("values", {})
        self._types = data.get("types", {})
        self._expiry = data.get("expiry", {})
        return True
