#!/usr/bin/env python
"""Test MiniKV implementation."""

from minikv import QueueServer, CommandError

def test_basic():
    server = QueueServer(use_gevent=False)
    
    # String operations
    assert server.kv_set("name", "Alice") == 1
    assert server.kv_get("name") == "Alice"
    assert server.kv_incr("counter") == 1
    assert server.kv_incr("counter") == 2
    assert server.kv_decr("counter") == 1
    assert server.kv_exists("name") == 1
    assert server.kv_exists("missing") == 0
    
    # List operations
    assert server.lpush("items", "a", "b") == 2
    assert server.kv_get("items") == ["b", "a"]
    assert server.rpush("items", "c") == 3
    assert server.lrange("items", 0, 2) == ["b", "a"]
    assert server.lpop("items") == "b"
    assert server.rpop("items") == "c"
    
    # Set operations
    assert server.sadd("tags", "python", "java") == 2
    assert len(server.smembers("tags")) == 2
    assert server.scard("tags") == 2
    assert server.srem("tags", "java") == 1
    assert server.scard("tags") == 1
    
    # Hash operations
    assert server.hset("user:1", "name", "Alice") == 1
    assert server.hset("user:1", "age", 30) == 1
    assert server.hget("user:1", "name") == "Alice"
    assert server.hgetall("user:1") == {"name": "Alice", "age": 30}
    assert server.hdel("user:1", "age") == 1
    
    # Bulk operations
    assert server.kv_mset({"k1": "v1", "k2": "v2"}, k3="v3") == 3
    assert server.kv_mget("k1", "k2", "k3", "missing") == ["v1", "v2", "v3", None]
    
    # Type checking
    try:
        server.lpush("name", "x")
        assert False, "Should raise CommandError"
    except CommandError:
        pass
    
    try:
        server.sadd("items", "x")
        assert False, "Should raise CommandError"
    except CommandError:
        pass
    
    # Persistence
    assert server.save_to_disk("test.pkl") == True
    assert server.restore_from_disk("test.pkl") == True
    assert server.kv_get("name") == "Alice"
    
    # Flush
    count = server.kv_flush()
    assert count > 0
    assert server.kv_get("name") is None
    
    print("All tests passed!")

if __name__ == "__main__":
    test_basic()