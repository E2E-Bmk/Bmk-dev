"""Quick smoke tests for minidynaconf."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

failed = 0

def check(name, actual, expected):
    global failed
    ok = actual == expected
    status = "OK" if ok else f"FAIL (got {actual!r}, expected {expected!r})"
    print(f"  [{status}] {name}")
    if not ok:
        failed += 1

print("=== Test 1: Basic defaults ===")
s = MiniDynaconf(defaults={"host": "localhost", "port": 5432})
check("attr access", s.host, "localhost")
check("int type preserved", type(s.port), int)
check("get()", s.get("host"), "localhost")
check("exists true", s.exists("host"), True)
check("exists false", s.exists("nonexistent"), False)
check("get default", s.get("nonexistent", "fallback"), "fallback")
check("as_dict keys", set(s.as_dict().keys()), {"HOST", "PORT"})

print("\n=== Test 2: Case insensitivity ===")
s = MiniDynaconf(defaults={"Database": {"Host": "db.local", "Port": 5432}})
check("lowercase attr", s.database.host, "db.local")
check("mixed case item", s["DATABASE.PORT"], 5432)
check("dotted get", s.get("database.host"), "db.local")
check("exists dotted", s.exists("DATABASE.HOST"), True)

print("\n=== Test 3: Item access / set / delete ===")
s = MiniDynaconf(defaults={"x": 1})
check("item get", s["x"], 1)
s["x"] = 2
check("after set", s.x, 2)
s.set("y", 3)
check("after set()", s.y, 3)
check("exists after set", s.exists("y"), True)
s.delete("x")
check("exists after delete", s.exists("x"), False)

print("\n=== Test 4: Nested merge ===")
s = MiniDynaconf(defaults={"db": {"host": "a", "port": 1}})
s.set("db.port", 2)
check("nested override", s.db.host, "a")
check("sibling preserved", s.db.port, 2)

print("\n=== Test 5: get with cast ===")
s = MiniDynaconf(defaults={"port": 5432})
check("get cast", s.get("port", cast=str), "5432")
check("value unchanged", s.port, 5432)

print("\n=== Test 6: Validator - required ===")
try:
    s = MiniDynaconf(validators=[Validator("name", required=True)])
    print("  [FAIL] Should have raised ValidationError")
    failed += 1
except ValidationError:
    print("  [OK] ValidationError raised for missing required key")

print("\n=== Test 7: Validator - default ===")
s = MiniDynaconf(validators=[Validator("timeout", default=30, is_type_of=int)])
check("validator default", s.timeout, 30)

print("\n=== Test 8: Validator - type check ===")
try:
    s = MiniDynaconf(
        defaults={"port": "not-a-number"},
        validators=[Validator("port", is_type_of=int)],
    )
    print("  [FAIL] Should have raised ValidationError")
    failed += 1
except ValidationError:
    print("  [OK] ValidationError for wrong type")

print("\n=== Test 9: Validator - condition ===")
s = MiniDynaconf(
    defaults={"port": 8080},
    validators=[Validator("port", condition=lambda v, s: 1024 <= v <= 65535)],
)
check("condition passes", s.port, 8080)

try:
    s2 = MiniDynaconf(
        defaults={"port": 80},
        validators=[Validator("port", condition=lambda v, s: 1024 <= v <= 65535)],
    )
    print("  [FAIL] Should have raised ValidationError")
    failed += 1
except ValidationError:
    print("  [OK] ValidationError for failed condition")

print("\n=== Test 10: as_dict deep copy ===")
s = MiniDynaconf(defaults={"x": [1, 2, 3]})
d = s.as_dict()
d["X"].append(4)
check("as_dict is a copy", s.x, [1, 2, 3])

print("\n=== Test 11: Falsey values ===")
s = MiniDynaconf(defaults={"flag": False, "count": 0, "name": ""})
check("False is existing", s.exists("flag"), True)
check("0 is existing", s.exists("count"), True)
check("empty string is existing", s.exists("name"), True)

print("\n=== Test 12: delete then access ===")
s = MiniDynaconf(defaults={"x": 1})
s.delete("x")
check("exists after delete", s.exists("x"), False)
check("get default after delete", s.get("x", 42), 42)
try:
    _ = s.x
    print("  [FAIL] Should have raised AttributeError")
    failed += 1
except AttributeError:
    print("  [OK] AttributeError for deleted key")

print("\n=== Test 13: Nested dot-path set ===")
s = MiniDynaconf()
s.set("a.b.c", 42)
check("nested set", s.a.b.c, 42)
check("as_dict nested", s.as_dict(), {"A": {"B": {"C": 42}}})

print("\n=== Test 14: update() ===")
s = MiniDynaconf(defaults={"a": 1})
s.update({"b": 2, "c.d": 3})
check("update b", s.b, 2)
check("update nested", s.c.d, 3)

print("\n=== Test 15: Reload ===")
s = MiniDynaconf(defaults={"x": 1})
s.set("x", 99)
check("before reload", s.x, 99)
s.reload()
check("after reload", s.x, 1)

print(f"\n{'='*40}")
print(f"Failed: {failed}")

if failed:
    sys.exit(1)
