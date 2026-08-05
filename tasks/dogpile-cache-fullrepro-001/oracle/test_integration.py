# Spec2Repo oracle - integration tests for dogpile-cache-fullrepro-001

import itertools
import json
import time

import pytest

from dogpile.cache import exception
from dogpile.cache import make_region
from dogpile.cache.api import CachedValue
from dogpile.cache.api import NO_VALUE
from dogpile.cache.api import CantDeserializeException
from dogpile.cache.proxy import ProxyBackend
from dogpile.cache.util import kwarg_function_key_generator

from conftest import ManglingBackend
from conftest import PublicDictBackend


@pytest.mark.depends_on("test_configure_memory_returns_same_region_and_enables_use")
def test_configure_from_config_builds_backend_with_prefixed_arguments():
    region = make_region()
    region.configure_from_config(
        {
            "cache.docs.backend": "spec.public_dict",
            "cache.docs.expiration_time": "45",
            "cache.docs.arguments.name": "cfg-one",
            "cache.docs.arguments.mode": "rw",
        },
        "cache.docs.",
    )
    region.set("cfg-key", "cfg-value")
    assert region.expiration_time == 45
    assert PublicDictBackend.store_for("cfg-one")
    assert region.get("cfg-key") == "cfg-value"
    assert region.backend.arguments["mode"] == "rw"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value", "test_delete_is_idempotent_and_removes_cached_value")
def test_user_key_mangler_is_applied_to_set_get_and_delete():
    physical = {}
    region = make_region(key_mangler=lambda key: "prefix:" + key).configure(
        "dogpile.cache.memory", arguments={"cache_dict": physical}
    )
    region.set("logical", "payload")
    assert "prefix:logical" in physical
    assert region.get("logical") == "payload"
    region.delete("logical")
    assert region.get("logical") is NO_VALUE


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_backend_key_mangler_is_adopted_when_region_has_no_user_mangler():
    region = make_region().configure("spec.mangling_dict", arguments={"name": "mangle"})
    region.set("item", "payload")
    assert "backend:item" in ManglingBackend.store_for("mangle")
    assert region.get("item") == "payload"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_region_key_mangler_overrides_backend_key_mangler():
    region = make_region(key_mangler=lambda key: "user:" + key).configure(
        "spec.mangling_dict", arguments={"name": "override"}
    )
    region.set("item", "payload")
    assert "user:item" in ManglingBackend.store_for("override")
    assert "backend:item" not in ManglingBackend.store_for("override")
    assert region.get("item") == "payload"


@pytest.mark.depends_on("test_set_multi_get_multi_preserves_requested_order")
def test_key_mangler_applies_to_multi_key_operations():
    physical = {}
    region = make_region(key_mangler=lambda key: "multi:" + key).configure(
        "dogpile.cache.memory", arguments={"cache_dict": physical}
    )
    region.set_multi({"a": "A", "b": "B"})
    assert sorted(physical) == ["multi:a", "multi:b"]
    assert region.get_multi(["b", "a"]) == ["B", "A"]
    region.delete_multi(["a", "b"])
    assert region.get_multi(["a", "b"]) == [NO_VALUE, NO_VALUE]


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_hard_invalidation_forces_next_get_or_create_regeneration(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    def creator():
        return f"version-{next(counter)}"

    assert region.get_or_create("invalidate-me", creator) == "version-1"
    now[0] += 1
    region.invalidate()
    assert region.get("invalidate-me") is NO_VALUE
    assert region.get_or_create("invalidate-me", creator) == "version-2"


@pytest.mark.depends_on("test_get_ignore_expiration_returns_stale_payload")
def test_ignore_expiration_bypasses_hard_invalidation_for_get(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    region = make_region().configure("dogpile.cache.memory")
    region.set("local-only", "old")
    now[0] += 1
    region.invalidate()
    assert region.get("local-only") is NO_VALUE
    assert region.get("local-only", ignore_expiration=True) == "old"


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_soft_invalidation_regenerates_when_expiration_is_available(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(time, "time", lambda: now[0])
    region = make_region().configure("dogpile.cache.memory", expiration_time=60)
    counter = itertools.count(1)

    def creator():
        return f"soft-{next(counter)}"

    assert region.get_or_create("soft-key", creator) == "soft-1"
    now[0] += 1
    region.invalidate(hard=False)
    assert region.get_or_create("soft-key", creator) == "soft-2"


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_soft_invalidation_without_expiration_raises_cache_exception():
    region = make_region().configure("dogpile.cache.memory")
    region.invalidate(hard=False)
    with pytest.raises(exception.DogpileCacheException):
        region.get_or_create("soft-error", lambda: "value")


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order", "test_region_set_and_get_round_trip_a_value")
def test_get_or_create_multi_generates_only_missing_keys_and_preserves_existing():
    region = make_region().configure("dogpile.cache.memory")
    region.set("b", "cached-b")
    seen = []

    def creator(*keys):
        seen.append(tuple(keys))
        return [f"fresh-{key}" for key in keys]

    assert region.get_or_create_multi(["a", "b", "c"], creator) == [
        "fresh-a",
        "cached-b",
        "fresh-c",
    ]
    assert seen == [("a", "c")]


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_get_or_create_multi_should_cache_fn_filters_each_generated_value():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    def creator(*keys):
        return [f"{key}-{next(counter)}" for key in keys]

    def should_cache(value):
        return not value.startswith("skip")

    assert region.get_or_create_multi(["keep", "skip"], creator, should_cache_fn=should_cache) == [
        "keep-1",
        "skip-2",
    ]
    assert region.get_or_create_multi(["keep", "skip"], creator, should_cache_fn=should_cache) == [
        "keep-1",
        "skip-3",
    ]


@pytest.mark.depends_on("test_get_value_metadata_returns_cached_value_object", "test_region_set_and_get_round_trip_a_value")
def test_metadata_projection_agrees_with_cached_payload_and_expiration():
    region = make_region().configure("dogpile.cache.memory")
    region.set("meta-view", {"kind": "invoice"})
    metadata = region.get_value_metadata("meta-view")
    assert metadata.payload == region.get("meta-view")
    assert region.get_value_metadata("meta-view", expiration_time=0) is None
    assert region.get_value_metadata("meta-view", expiration_time=0, ignore_expiration=True).payload == {"kind": "invoice"}


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_cache_on_arguments_caches_results_per_argument_tuple():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_on_arguments()
    def build(left, right):
        return f"{left}:{right}:{next(counter)}"

    assert build("a", "b") == "a:b:1"
    assert build("a", "b") == "a:b:1"
    assert build("b", "a") == "b:a:2"


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value", "test_delete_is_idempotent_and_removes_cached_value")
def test_cache_on_arguments_invalidate_targets_one_argument_tuple():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_on_arguments()
    def build(token):
        return f"{token}-{next(counter)}"

    assert build("x") == "x-1"
    assert build("y") == "y-2"
    build.invalidate("x")
    assert build("x") == "x-3"
    assert build("y") == "y-2"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_cache_on_arguments_helper_methods_share_the_region_key():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_on_arguments()
    def build(token):
        return f"made-{token}-{next(counter)}"

    assert build("q") == "made-q-1"
    build.set("manual-q", "q")
    assert build.get("q") == "manual-q"
    assert build("q") == "manual-q"
    assert build.refresh("q") == "made-q-2"
    assert build.original("q") == "made-q-3"
    assert build("q") == "made-q-2"


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_cache_on_arguments_accepts_equivalent_keyword_calls_for_wrapped_signature():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_on_arguments()
    def build(left, right):
        return f"{left + right}:{next(counter)}"

    assert build(1, 2) == "3:1"
    assert build(1, right=2) == "3:1"


@pytest.mark.depends_on("test_kwarg_function_key_generator_sorts_argument_names_and_uses_defaults")
def test_cache_on_arguments_with_kwarg_generator_accepts_equivalent_kwarg_calls():
    region = make_region(function_key_generator=kwarg_function_key_generator).configure(
        "dogpile.cache.memory"
    )
    counter = itertools.count(1)

    @region.cache_on_arguments()
    def build(left, right=3):
        return f"{left + right}:{next(counter)}"

    assert build(2, right=4) == "6:1"
    assert build(right=4, left=2) == "6:1"
    assert build(2) == "5:2"


@pytest.mark.depends_on("test_cache_backend_from_config_dict_filters_prefix")
def test_cache_on_arguments_namespaces_isolate_same_callable_arguments():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    def raw(value):
        return f"{value}-{next(counter)}"

    first = region.cache_on_arguments(namespace="first")(raw)
    second = region.cache_on_arguments(namespace="second")(raw)
    assert first("same") == "same-1"
    assert second("same") == "same-2"
    assert first("same") == "same-1"
    assert second("same") == "same-2"


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_cache_multi_on_arguments_caches_subset_and_invalidates_one_key():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_multi_on_arguments()
    def build(*keys):
        return [f"{key}-{next(counter)}" for key in keys]

    assert build("a", "b", "c") == ["a-1", "b-2", "c-3"]
    assert build("a", "d", "c") == ["a-1", "d-4", "c-3"]
    build.invalidate("a")
    assert build("a", "c") == ["a-5", "c-3"]


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_cache_multi_on_arguments_asdict_preserves_keyed_result_shape():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_multi_on_arguments(asdict=True)
    def build(*keys):
        return {key: f"{key}-{next(counter)}" for key in keys if key != "omit"}

    assert build("a", "omit", "b") == {"a": "a-1", "b": "b-2"}
    assert build("a", "c", "omit") == {"a": "a-1", "c": "c-3"}
    build.set({"c": "manual-c", "omit": "manual-omit"})
    assert build("c", "omit") == {"c": "manual-c", "omit": "manual-omit"}


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_cache_multi_on_arguments_refresh_updates_selected_cached_keys():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_multi_on_arguments()
    def build(*keys):
        return [f"{key}-{next(counter)}" for key in keys]

    assert build("x", "y") == ["x-1", "y-2"]
    assert build.refresh("x") == ["x-3"]
    assert build("x", "y") == ["x-3", "y-2"]


@pytest.mark.depends_on("test_function_key_generator_uses_module_function_namespace_and_positional_values")
def test_custom_function_key_generator_controls_decorator_cache_identity():
    def first_arg_only(namespace, fn, **kw):
        def generate_key(*args, **kwargs):
            return f"{namespace}:{args[0]}"

        return generate_key

    region = make_region(function_key_generator=first_arg_only).configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_on_arguments(namespace="custom")
    def build(user_id, field):
        return f"{user_id}:{field}:{next(counter)}"

    assert build(10, "name") == "10:name:1"
    assert build(10, "email") == "10:name:1"
    assert build(11, "email") == "11:email:2"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_proxy_backend_can_count_and_delegate_region_operations():
    class CountingProxy(ProxyBackend):
        def __init__(self):
            self.events = []
            super().__init__()

        def set(self, key, value):
            self.events.append(("set", key))
            return self.proxied.set(key, value)

        def get(self, key):
            self.events.append(("get", key))
            return self.proxied.get(key)

    proxy = CountingProxy()
    region = make_region().configure("dogpile.cache.memory", wrap=[proxy])
    region.set("proxied", "value")
    assert region.get("proxied") == "value"
    assert proxy.events == [("set", "proxied"), ("get", "proxied")]


@pytest.mark.depends_on("test_configure_memory_returns_same_region_and_enables_use")
def test_proxy_chain_exposes_actual_underlying_backend():
    first = ProxyBackend()
    second = ProxyBackend()
    region = make_region().configure("dogpile.cache.memory", wrap=[first, second])
    assert region.backend is first
    assert first.proxied is second
    assert region.actual_backend is second.proxied
    region.set("chain", "ok")
    assert region.get("chain") == "ok"


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_proxy_set_multi_must_not_mutate_values_returned_by_get_or_create_multi():
    class UpperPayloadProxy(ProxyBackend):
        def set_multi(self, mapping):
            copied = {
                key: CachedValue(value.payload.upper(), value.metadata)
                for key, value in mapping.items()
            }
            return self.proxied.set_multi(copied)

    region = make_region().configure("dogpile.cache.memory", wrap=[UpperPayloadProxy])

    def creator(*keys):
        return [key.lower() for key in keys]

    assert region.get_or_create_multi(["aa", "bb"], creator) == ["aa", "bb"]
    assert region.get_multi(["aa", "bb"]) == ["AA", "BB"]


@pytest.mark.depends_on("test_configure_memory_returns_same_region_and_enables_use")
def test_registered_public_backend_is_loaded_by_region_configuration():
    region = make_region().configure("spec.public_dict", arguments={"name": "registered"})
    region.set("registered-key", "registered-value")
    assert PublicDictBackend.store_for("registered")
    assert region.get("registered-key") == "registered-value"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value", "test_configure_memory_returns_same_region_and_enables_use")
def test_dbm_backend_persists_values_across_regions(tmp_path):
    filename = str(tmp_path / "cache-file.dbm")
    first = make_region().configure(
        "dogpile.cache.dbm",
        arguments={"filename": filename, "rw_lockfile": False, "dogpile_lockfile": False},
    )
    first.set("disk-key", {"answer": 42})
    second = make_region().configure(
        "dogpile.cache.dbm",
        arguments={"filename": filename, "rw_lockfile": False, "dogpile_lockfile": False},
    )
    assert second.get("disk-key") == {"answer": 42}


@pytest.mark.depends_on("test_delete_is_idempotent_and_removes_cached_value")
def test_dbm_backend_delete_is_visible_to_later_regions(tmp_path):
    filename = str(tmp_path / "cache-delete.dbm")
    first = make_region().configure(
        "dogpile.cache.dbm",
        arguments={"filename": filename, "rw_lockfile": False, "dogpile_lockfile": False},
    )
    first.set("disk-key", "gone-soon")
    first.delete("disk-key")
    second = make_region().configure(
        "dogpile.cache.dbm",
        arguments={"filename": filename, "rw_lockfile": False, "dogpile_lockfile": False},
    )
    assert second.get("disk-key") is NO_VALUE


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_region_serializer_and_deserializer_round_trip_payloads():
    region = make_region(
        serializer=lambda payload: json.dumps(payload).encode("utf-8"),
        deserializer=lambda payload: json.loads(payload.decode("utf-8")),
    ).configure("dogpile.cache.memory")
    original = {"numbers": [1, 2, 3]}
    region.set("serialized", original)
    original["numbers"].append(4)
    assert region.get("serialized") == {"numbers": [1, 2, 3]}


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_cant_deserialize_exception_causes_regeneration():
    calls = itertools.count(1)

    def deserializer(payload):
        if b'"old"' in payload:
            raise CantDeserializeException()
        return json.loads(payload.decode("utf-8"))

    region = make_region(
        serializer=lambda payload: json.dumps(payload).encode("utf-8"),
        deserializer=deserializer,
    ).configure("dogpile.cache.memory")
    region.set("broken-old", {"old": True})

    def creator():
        return {"fresh": next(calls)}

    assert region.get_or_create("broken-old", creator) == {"fresh": 1}
    assert region.get("broken-old") == {"fresh": 1}


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_async_creation_runner_refreshes_stale_value_and_returns_old_value_first():
    events = []

    def runner(cache, key, creator, mutex):
        events.append(("runner", key))
        try:
            cache.set(key, creator())
        finally:
            mutex.release()

    region = make_region(async_creation_runner=runner).configure(
        "dogpile.cache.memory", expiration_time=0
    )
    counter = itertools.count(1)

    def creator():
        return f"async-{next(counter)}"

    assert region.get_or_create("async-key", creator) == "async-1"
    assert region.get_or_create("async-key", creator) == "async-1"
    assert events == [("runner", "async-key")]
    assert region.get("async-key", ignore_expiration=True) == "async-2"


@pytest.mark.depends_on("test_region_set_and_get_round_trip_a_value")
def test_memory_pickle_backend_returns_independent_payload_copy():
    region = make_region().configure("dogpile.cache.memory_pickle")
    original = {"items": ["first"]}
    region.set("copy-key", original)
    original["items"].append("second")
    assert region.get("copy-key") == {"items": ["first"]}


@pytest.mark.depends_on("test_get_or_create_creates_once_then_reuses_cached_value")
def test_decorated_method_ignores_self_for_default_cache_key():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    class Service:
        @region.cache_on_arguments()
        def load(self, token):
            return f"{token}-{next(counter)}"

    first = Service()
    second = Service()
    assert first.load("shared") == "shared-1"
    assert second.load("shared") == "shared-1"


@pytest.mark.depends_on("test_get_or_create_multi_returns_values_in_input_order")
def test_cache_multi_on_arguments_should_cache_fn_filters_dict_values():
    region = make_region().configure("dogpile.cache.memory")
    counter = itertools.count(1)

    @region.cache_multi_on_arguments(asdict=True, should_cache_fn=lambda value: not value.endswith("-skip"))
    def build(*keys):
        return {
            key: f"{key}-{next(counter)}" + ("-skip" if key == "volatile" else "")
            for key in keys
        }

    first = build("stable", "volatile")
    second = build("stable", "volatile")
    assert first["stable"] == second["stable"]
    assert first["volatile"] != second["volatile"]
