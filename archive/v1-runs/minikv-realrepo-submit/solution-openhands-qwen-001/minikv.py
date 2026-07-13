"""
MiniKV - In-memory data structure store library.

Provides QueueServer class that stores strings/numbers, lists, sets, and hashes
in a single key namespace with type-tagged state.
"""

import pickle
import time
from typing import Any


class CommandError(Exception):
    """Raised for type mismatches and invalid operations."""
    pass


class QueueServer:
    """
    In-memory key-value store supporting strings, lists, sets, and hashes.
    
    Every key has one canonical type at a time, with type detection based on
    the value stored: dict->HASH, list->QUEUE, set->SET, others->KV.
    """
    
    # Type tags
    KV = "KV"
    QUEUE = "QUEUE"
    SET = "SET"
    HASH = "HASH"
    
    def __init__(self, use_gevent: bool = False):
        """Create a new data store instance.
        
        Args:
            use_gevent: Ignored for this task; always pass False.
        """
        # Main storage: key -> (value, type_tag, expiry_time_or_None)
        self._store: dict[str, tuple[Any, str, float | None]] = {}
        self._use_gevent = use_gevent
    
    def _get_entry(self, key: str) -> tuple[Any, str, float | None] | None:
        """Get store entry if exists and not expired, applying lazy expiration."""
        if key not in self._store:
            return None
        
        value, type_tag, expiry = self._store[key]
        
        # Lazy expiration check
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None
        
        return (value, type_tag, expiry)
    
    def _delete_expired(self, key: str) -> bool:
        """Delete key if expired. Returns True if deleted."""
        if key not in self._store:
            return False
        
        value, type_tag, expiry = self._store[key]
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return True
        return False
    
    def _detect_type(self, value: Any) -> str:
        """Detect type tag from value."""
        if isinstance(value, dict):
            return self.HASH
        elif isinstance(value, list):
            return self.QUEUE
        elif isinstance(value, set):
            return self.SET
        else:
            return self.KV
    
    # ==================== String and Scalar Operations ====================
    
    def kv_set(self, key: str, value: Any) -> int:
        """Store a value.
        
        Type is auto-detected: dict->HASH, list->QUEUE, set->SET, others->KV.
        Overwrites any previous value, type, and expiry.
        
        Returns:
            1
        """
        type_tag = self._detect_type(value)
        self._store[key] = (value, type_tag, None)
        return 1
    
    def kv_get(self, key: str) -> Any | None:
        """Return the stored value, or None if key doesn't exist or expired."""
        entry = self._get_entry(key)
        if entry is None:
            return None
        value, _, _ = entry
        return value
    
    def kv_delete(self, key: str) -> int:
        """Remove the key, including type and expiry metadata.
        
        Returns:
            1 if deleted, 0 if not found.
        """
        if self._delete_expired(key):
            return 1
        if key in self._store:
            del self._store[key]
            return 1
        return 0
    
    def kv_exists(self, key: str) -> int:
        """Return 1 if key exists and not expired, otherwise 0."""
        entry = self._get_entry(key)
        return 1 if entry is not None else 0
    
    def kv_incr(self, key: str) -> int | float:
        """Increment a numeric KV value by 1.
        
        If key doesn't exist, creates it at 0 then increments to 1.
        Raises CommandError on non-numeric values or wrong types.
        
        Returns:
            The new value.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new key starting at 0, then increment to 1
            self._store[key] = (1, self.KV, None)
            return 1
        
        value, type_tag, expiry = entry
        
        if type_tag != self.KV:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if not isinstance(value, (int, float)):
            raise CommandError("ERR value is not an integer or float")
        
        new_value = value + 1
        self._store[key] = (new_value, self.KV, expiry)
        return new_value
    
    def kv_decr(self, key: str) -> int | float:
        """Decrement a numeric KV value by 1.
        
        If key doesn't exist, creates it at 0 then decrements to -1.
        Raises CommandError on non-numeric values or wrong types.
        
        Returns:
            The new value.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new key starting at 0, then decrement to -1
            self._store[key] = (-1, self.KV, None)
            return -1
        
        value, type_tag, expiry = entry
        
        if type_tag != self.KV:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if not isinstance(value, (int, float)):
            raise CommandError("ERR value is not an integer or float")
        
        new_value = value - 1
        self._store[key] = (new_value, self.KV, expiry)
        return new_value
    
    # ==================== Bulk Operations ====================
    
    def kv_mset(self, __data: dict | None = None, **kwargs) -> int:
        """Set multiple keys from a dict and/or keyword arguments.
        
        Returns:
            Count of keys set.
        """
        count = 0
        
        if __data is not None:
            for key, value in __data.items():
                self.kv_set(key, value)
                count += 1
        
        for key, value in kwargs.items():
            self.kv_set(key, value)
            count += 1
        
        return count
    
    def kv_mget(self, *keys) -> list:
        """Return a list of direct-read values in the same order as requested keys.
        
        Missing or expired keys appear as None.
        """
        return [self.kv_get(key) for key in keys]
    
    # ==================== List Operations ====================
    
    def lpush(self, key: str, *values) -> int:
        """Prepend values to the head of a list.
        
        Creates the list if it doesn't exist. Values applied in argument order.
        
        Returns:
            Number of values pushed.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new list
            new_list = list(values)
            self._store[key] = (new_list, self.QUEUE, None)
            return len(values)
        
        value, type_tag, expiry = entry
        
        if type_tag != self.QUEUE:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        # Prepend in argument order (so lpush("q", "a", "b") gives ["b", "a", ...])
        for v in reversed(values):
            value.insert(0, v)
        
        self._store[key] = (value, self.QUEUE, expiry)
        return len(value)
    
    def rpush(self, key: str, *values) -> int:
        """Append values to the tail.
        
        Creates the list if it doesn't exist.
        
        Returns:
            Number of values pushed.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new list
            new_list = list(values)
            self._store[key] = (new_list, self.QUEUE, None)
            return len(values)
        
        value, type_tag, expiry = entry
        
        if type_tag != self.QUEUE:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        value.extend(values)
        self._store[key] = (value, self.QUEUE, expiry)
        return len(value)
    
    def lpop(self, key: str) -> Any | None:
        """Remove and return the first element.
        
        Returns:
            First element, or None if list is empty or missing.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return None
        
        value, type_tag, expiry = entry
        
        if type_tag != self.QUEUE:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if not value:
            return None
        
        result = value.pop(0)
        self._store[key] = (value, self.QUEUE, expiry)
        return result
    
    def rpop(self, key: str) -> Any | None:
        """Remove and return the last element.
        
        Returns:
            Last element, or None if list is empty or missing.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return None
        
        value, type_tag, expiry = entry
        
        if type_tag != self.QUEUE:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if not value:
            return None
        
        result = value.pop()
        self._store[key] = (value, self.QUEUE, expiry)
        return result
    
    def lrange(self, key: str, start: int, end: int | None = None) -> list:
        """Return a list slice using Python slice semantics [start:end].
        
        Args:
            key: The list key
            start: Start index
            end: End index (None means "to the end")
        
        Returns:
            List slice, or [] for missing keys.
        
        Raises:
            CommandError: On non-list keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return []
        
        value, type_tag, expiry = entry
        
        if type_tag != self.QUEUE:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        # Python slice semantics
        return list(value[start:end])
    
    # ==================== Set Operations ====================
    
    def sadd(self, key: str, *members) -> int:
        """Add members to a set.
        
        Creates the set if it doesn't exist.
        
        Returns:
            New cardinality.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new set
            new_set = set(members)
            self._store[key] = (new_set, self.SET, None)
            return len(new_set)
        
        value, type_tag, expiry = entry
        
        if type_tag != self.SET:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        value.update(members)
        self._store[key] = (value, self.SET, expiry)
        return len(value)
    
    def srem(self, key: str, *members) -> int:
        """Remove members from set.
        
        Returns:
            Count of members actually removed.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return 0
        
        value, type_tag, expiry = entry
        
        if type_tag != self.SET:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        removed = 0
        for member in members:
            if member in value:
                value.remove(member)
                removed += 1
        
        self._store[key] = (value, self.SET, expiry)
        return removed
    
    def smembers(self, key: str) -> set:
        """Return the internal set object.
        
        If key doesn't exist, creates an empty set first.
        
        Returns:
            The set object.
        
        Raises:
            CommandError: On non-set keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create empty set
            new_set = set()
            self._store[key] = (new_set, self.SET, None)
            return new_set
        
        value, type_tag, expiry = entry
        
        if type_tag != self.SET:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return value
    
    def scard(self, key: str) -> int:
        """Return the cardinality.
        
        If key doesn't exist, creates an empty set and returns 0.
        
        Returns:
            Number of members in set.
        
        Raises:
            CommandError: On non-set keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create empty set
            new_set = set()
            self._store[key] = (new_set, self.SET, None)
            return 0
        
        value, type_tag, expiry = entry
        
        if type_tag != self.SET:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return len(value)
    
    # ==================== Hash Operations ====================
    
    def hset(self, key: str, field: str, value: Any) -> int:
        """Set a field in hash.
        
        Creates the hash if it doesn't exist.
        
        Returns:
            1
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create new hash
            new_dict = {field: value}
            self._store[key] = (new_dict, self.HASH, None)
            return 1
        
        value_store, type_tag, expiry = entry
        
        if type_tag != self.HASH:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        value_store[field] = value
        self._store[key] = (value_store, self.HASH, expiry)
        return 1
    
    def hget(self, key: str, field: str) -> Any | None:
        """Return the field value.
        
        Returns:
            Field value, or None if hash or field doesn't exist.
        
        Raises:
            CommandError: On non-hash keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return None
        
        value, type_tag, expiry = entry
        
        if type_tag != self.HASH:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return value.get(field)
    
    def hdel(self, key: str, field: str) -> int:
        """Delete a field from hash.
        
        Returns:
            1 if deleted, 0 if not found.
        
        Raises:
            CommandError: On non-hash keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return 0
        
        value, type_tag, expiry = entry
        
        if type_tag != self.HASH:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        if field in value:
            del value[field]
            self._store[key] = (value, self.HASH, expiry)
            return 1
        
        return 0
    
    def hgetall(self, key: str) -> dict:
        """Return the internal dict object.
        
        If key doesn't exist, creates an empty hash first.
        
        Returns:
            The dict object.
        
        Raises:
            CommandError: On non-hash keys.
        """
        entry = self._get_entry(key)
        
        if entry is None:
            # Create empty hash
            new_dict = {}
            self._store[key] = (new_dict, self.HASH, None)
            return new_dict
        
        value, type_tag, expiry = entry
        
        if type_tag != self.HASH:
            raise CommandError(f"WRONGTYPE Operation against a key holding the wrong kind of value")
        
        return value
    
    # ==================== Key Management ====================
    
    def expire(self, key: str, nseconds: int) -> None:
        """Set a timeout in seconds for a live key.
        
        Calling for a missing key is a no-op.
        
        Returns:
            None
        """
        entry = self._get_entry(key)
        
        if entry is None:
            return None
        
        value, type_tag, expiry = entry
        self._store[key] = (value, type_tag, time.time() + nseconds)
        return None
    
    def kv_flush(self) -> int:
        """Remove all live keys and metadata.
        
        Returns:
            Number of live keys removed.
        """
        count = 0
        now = time.time()
        keys_to_delete = []
        
        for key, (value, type_tag, expiry) in self._store.items():
            if expiry is None or expiry > now:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._store[key]
            count += 1
        
        return count
    
    def save_to_disk(self, filename: str) -> bool:
        """Persist the entire database state to a file using pickle.
        
        Returns:
            True
        """
        # Clean up expired keys before saving
        now = time.time()
        live_store = {}
        for key, (value, type_tag, expiry) in self._store.items():
            if expiry is None or expiry > now:
                live_store[key] = (value, type_tag, expiry)
        
        with open(filename, 'wb') as f:
            pickle.dump(live_store, f)
        return True
    
    def restore_from_disk(self, filename: str) -> bool:
        """Restore database state from a pickle file.
        
        Returns:
            True if restored, False if file doesn't exist.
        """
        import os
        if not os.path.exists(filename):
            return False
        
        with open(filename, 'rb') as f:
            self._store = pickle.load(f)
        return True