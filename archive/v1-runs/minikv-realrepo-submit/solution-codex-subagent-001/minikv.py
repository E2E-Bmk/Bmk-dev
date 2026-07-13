"""A small in-memory key-value store."""

from __future__ import annotations

import os
import pickle
import time


class CommandError(Exception):
    """Raised when a command cannot be applied to the current key type."""


class QueueServer:
    KV = "kv"
    QUEUE = "queue"
    SET = "set"
    HASH = "hash"

    def __init__(self, use_gevent: bool = False):
        self._values = {}
        self._types = {}
        self._expires = {}

    def _now(self):
        return time.time()

    def _purge_if_expired(self, key):
        expires_at = self._expires.get(key)
        if expires_at is not None and expires_at <= self._now():
            self._delete_key(key)
            return True
        return False

    def _delete_key(self, key):
        existed = key in self._values
        self._values.pop(key, None)
        self._types.pop(key, None)
        self._expires.pop(key, None)
        return existed

    def _exists_live(self, key):
        return key in self._values and not self._purge_if_expired(key)

    def _type_for_value(self, value):
        if isinstance(value, dict):
            return self.HASH
        if isinstance(value, list):
            return self.QUEUE
        if isinstance(value, set):
            return self.SET
        return self.KV

    def _require_type(self, key, expected_type):
        if not self._exists_live(key):
            return False
        actual_type = self._types.get(key)
        if actual_type != expected_type:
            raise CommandError(
                f"Key {key!r} has type {actual_type}, expected {expected_type}"
            )
        return True

    def kv_set(self, key, value):
        self._values[key] = value
        self._types[key] = self._type_for_value(value)
        self._expires.pop(key, None)
        return 1

    def kv_get(self, key):
        if not self._exists_live(key):
            return None
        return self._values[key]

    def kv_delete(self, key):
        if not self._exists_live(key):
            return 0
        self._delete_key(key)
        return 1

    def kv_exists(self, key):
        return 1 if self._exists_live(key) else 0

    def _change_number(self, key, amount):
        if not self._exists_live(key):
            self._values[key] = 0
            self._types[key] = self.KV

        self._require_type(key, self.KV)
        value = self._values[key]
        if not isinstance(value, (int, float)):
            raise CommandError(f"Key {key!r} does not contain a numeric value")

        value += amount
        self._values[key] = value
        return value

    def kv_incr(self, key):
        return self._change_number(key, 1)

    def kv_decr(self, key):
        return self._change_number(key, -1)

    def kv_mset(self, __data=None, **kwargs):
        data = {}
        if __data is not None:
            data.update(__data)
        data.update(kwargs)
        for key, value in data.items():
            self.kv_set(key, value)
        return len(data)

    def kv_mget(self, *keys):
        return [self.kv_get(key) for key in keys]

    def _ensure_list(self, key, create=False):
        if not self._exists_live(key):
            if not create:
                return None
            self._values[key] = []
            self._types[key] = self.QUEUE
        else:
            self._require_type(key, self.QUEUE)
        return self._values[key]

    def lpush(self, key, *values):
        queue = self._ensure_list(key, create=True)
        for value in values:
            queue.insert(0, value)
        return len(values)

    def rpush(self, key, *values):
        queue = self._ensure_list(key, create=True)
        queue.extend(values)
        return len(values)

    def lpop(self, key):
        queue = self._ensure_list(key)
        if not queue:
            return None
        return queue.pop(0)

    def rpop(self, key):
        queue = self._ensure_list(key)
        if not queue:
            return None
        return queue.pop()

    def lrange(self, key, start, end=None):
        queue = self._ensure_list(key)
        if queue is None:
            return []
        return queue[start:end]

    def _ensure_set(self, key, create=False):
        if not self._exists_live(key):
            if not create:
                return None
            self._values[key] = set()
            self._types[key] = self.SET
        else:
            self._require_type(key, self.SET)
        return self._values[key]

    def sadd(self, key, *members):
        values = self._ensure_set(key, create=True)
        values.update(members)
        return len(values)

    def srem(self, key, *members):
        values = self._ensure_set(key)
        if values is None:
            return 0
        removed = 0
        for member in members:
            if member in values:
                values.remove(member)
                removed += 1
        return removed

    def smembers(self, key):
        return self._ensure_set(key, create=True)

    def scard(self, key):
        return len(self._ensure_set(key, create=True))

    def _ensure_hash(self, key, create=False):
        if not self._exists_live(key):
            if not create:
                return None
            self._values[key] = {}
            self._types[key] = self.HASH
        else:
            self._require_type(key, self.HASH)
        return self._values[key]

    def hset(self, key, field, value):
        values = self._ensure_hash(key, create=True)
        values[field] = value
        return 1

    def hget(self, key, field):
        values = self._ensure_hash(key)
        if values is None:
            return None
        return values.get(field)

    def hdel(self, key, field):
        values = self._ensure_hash(key)
        if values is None:
            return 0
        if field not in values:
            return 0
        del values[field]
        return 1

    def hgetall(self, key):
        return self._ensure_hash(key, create=True)

    def expire(self, key, nseconds):
        if self._exists_live(key):
            self._expires[key] = self._now() + nseconds
        return None

    def kv_flush(self):
        count = len(self._values)
        self._values.clear()
        self._types.clear()
        self._expires.clear()
        return count

    def save_to_disk(self, filename):
        state = {
            "values": self._values,
            "types": self._types,
            "expires": self._expires,
        }
        with open(filename, "wb") as file:
            pickle.dump(state, file, protocol=pickle.HIGHEST_PROTOCOL)
        return True

    def restore_from_disk(self, filename):
        if not os.path.exists(filename):
            return False
        with open(filename, "rb") as file:
            state = pickle.load(file)
        self._values = state.get("values", {})
        self._types = state.get("types", {})
        self._expires = state.get("expires", {})
        return True
