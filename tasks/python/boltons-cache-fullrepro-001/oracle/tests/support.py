from __future__ import annotations

import copy
import importlib


def api(): return importlib.import_module("boltons.cachefabric")


def fabric(*, shards=("s0",), layers=("base", "tenant", "hot"), capacity=6, admission=30, eviction=12, attempts=3):
    return api().CacheFabric(shards=shards, layers=layers, capacity=capacity, admission_budget=admission, eviction_budget=eviction, max_attempts=attempts)


def put(c, key, value, *, layer="base", owner="alice", cost=1, depends_on=()):
    return c.put(key, value, layer=layer, owner=owner, cost=cost, depends_on=depends_on, expected_generation=c.topology()["generation"], expected_revision=c.revision())


def begin(c, name="tx", owner="alice"):
    return c.begin(name, owner=owner, expected_generation=c.topology()["generation"], expected_revision=c.revision())


def fails(error, function):
    try: function()
    except error: return
    raise AssertionError(f"expected {error.__name__}")


def unchanged(c, error, function):
    before=copy.deepcopy(c.snapshot()); fails(error,function); assert c.snapshot()==before


def key_for(c, shard, prefix="key"):
    for index in range(10000):
        candidate=f"{prefix}-{index}"
        if c.route(candidate)["shard"]==shard:return candidate
    raise AssertionError("unable to find deterministic routed key")

