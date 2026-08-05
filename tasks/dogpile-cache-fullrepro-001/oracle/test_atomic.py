# Spec2Repo oracle - atomic tests for dogpile-cache-fullrepro-001

import datetime
import hashlib
import itertools
import threading
import time

import pytest

from dogpile import Lock
from dogpile import NeedRegenerationException
from dogpile.cache import CacheRegion
from dogpile.cache import exception
from dogpile.cache import make_region
from dogpile.cache.api import CacheBackend
from dogpile.cache.api import CachedValue
from dogpile.cache.api import NO_VALUE
from dogpile.cache.backends.memory import MemoryBackend
from dogpile.cache.backends.null import NullBackend
from dogpile.cache.util import function_key_generator
from dogpile.cache.util import function_multi_key_generator
from dogpile.cache.util import kwarg_function_key_generator
from dogpile.cache.util import length_conditional_mangler
from dogpile.cache.util import sha1_mangle_key


def test_no_value_is_false_and_distinct_from_none():
    assert not NO_VALUE
    assert NO_VALUE is not None
    assert NO_VALUE.payload is NO_VALUE


def test_cached_value_exposes_payload_metadata_and_dynamic_age():
    cached = CachedValue("payload-a", {"ct": time.time() - 0.01, "v": 2})
    assert cached.payload == "payload-a"
    assert cached.cached_time == cached.metadata["ct"]
    assert cached.age >= 0


def test_make_region_preserves_public_name():
    region = make_region(name="reports")
    assert region.name == "reports"
    assert region.is_configured is False


def test_unconfigured_region_reports_state_and_rejects_backend_access():
    region = CacheRegion()
    assert region.is_configured is False
    with pytest.raises(exception.RegionNotConfigured):
        region.backend


def test_configure_memory_returns_same_region_and_enables_use():
    region = make_region()
    configured = region.configure("dogpile.cache.memory")
    assert configured is region
    assert region.is_configured is True
    region.set("alpha", 13)
    assert region.get("alpha") == 13


def test_configure_unknown_backend_raises_plugin_not_found():
    with pytest.raises(exception.PluginNotFound):
        make_region().configure("not.a.cache.backend")


def test_duplicate_configure_requires_replace_flag():
    region = make_region().configure("dogpile.cache.memory")
    with pytest.raises(exception.RegionAlreadyConfigured):
        region.configure("dogpile.cache.memory")


def test_replace_existing_backend_allows_reconfiguration():
    region = make_region().configure("dogpile.cache.null")
    region.configure("dogpile.cache.memory", replace_existing_backend=True)
    region.set("after-replace", "stored")
    assert region.get("after-replace") == "stored"


def test_invalid_expiration_type_raises_validation_error():
    with pytest.raises(exception.ValidationError):
        make_region().configure("dogpile.cache.memory", expiration_time=object())


def test_timedelta_expiration_is_converted_to_seconds():
    region = make_region().configure(
        "dogpile.cache.memory", expiration_time=datetime.timedelta(minutes=2)
    )
    assert region.expiration_time == 120


def test_region_set_and_get_round_trip_a_value(fresh_region):
    region = fresh_region()
    region.set("profile:42", {"name": "Ada", "visits": 4})
    assert region.get("profile:42") == {"name": "Ada", "visits": 4}


def test_missing_key_returns_no_value_sentinel(fresh_region):
    assert fresh_region().get("absent-key") is NO_VALUE


def test_delete_is_idempotent_and_removes_cached_value(fresh_region):
    region = fresh_region()
    region.set("session-1", "open")
    region.delete("session-1")
    region.delete("session-1")
    assert region.get("session-1") is NO_VALUE


def test_set_multi_get_multi_preserves_requested_order(fresh_region):
    region = fresh_region()
    region.set_multi({"east": 1, "west": 2})
    assert region.get_multi(["west", "missing", "east"]) == [2, NO_VALUE, 1]


def test_get_multi_empty_sequence_returns_empty_list(fresh_region):
    assert fresh_region().get_multi([]) == []


def test_delete_multi_removes_existing_and_ignores_missing(fresh_region):
    region = fresh_region()
    region.set_multi({"a": "A", "b": "B", "c": "C"})
    region.delete_multi(["b", "z"])
    assert region.get_multi(["a", "b", "c"]) == ["A", NO_VALUE, "C"]


def test_get_value_metadata_returns_cached_value_object(fresh_region):
    region = fresh_region()
    region.set("metadata-key", "metadata-payload")
    metadata = region.get_value_metadata("metadata-key")
    assert isinstance(metadata, CachedValue)
    assert metadata.payload == "metadata-payload"
    assert isinstance(metadata.cached_time, float)


def test_get_value_metadata_returns_none_for_missing_key(fresh_region):
    assert fresh_region().get_value_metadata("unknown") is None


def test_get_honors_zero_expiration_time(fresh_region):
    region = fresh_region()
    region.set("soon-stale", "old")
    assert region.get("soon-stale", expiration_time=0) is NO_VALUE


def test_get_ignore_expiration_returns_stale_payload(fresh_region):
    region = fresh_region()
    region.set("stale-but-readable", "old")
    assert region.get("stale-but-readable", expiration_time=0) is NO_VALUE
    assert region.get("stale-but-readable", expiration_time=0, ignore_expiration=True) == "old"


def test_get_or_create_creates_once_then_reuses_cached_value(fresh_region):
    region = fresh_region()
    counter = itertools.count(1)

    def creator():
        return f"value-{next(counter)}"

    assert region.get_or_create("create-once", creator) == "value-1"
    assert region.get_or_create("create-once", creator) == "value-1"


def test_get_or_create_passes_creator_args_when_generation_is_needed(fresh_region):
    region = fresh_region()

    def creator(prefix, *, number):
        return f"{prefix}-{number}"

    assert region.get_or_create(
        "creator-args", creator, creator_args=(("item",), {"number": 7})
    ) == "item-7"


def test_get_or_create_should_cache_false_returns_without_storing(fresh_region):
    region = fresh_region()
    counter = itertools.count(1)

    def creator():
        return next(counter)

    assert region.get_or_create("skip-cache", creator, should_cache_fn=lambda value: False) == 1
    assert region.get_or_create("skip-cache", creator, should_cache_fn=lambda value: False) == 2


def test_get_or_create_negative_one_expiration_means_no_expiration(fresh_region):
    region = fresh_region()
    counter = itertools.count(1)

    def creator():
        return next(counter)

    assert region.get_or_create("never-expire", creator) == 1
    assert region.get_or_create("never-expire", creator, expiration_time=-1) == 1


def test_get_or_create_multi_returns_values_in_input_order(fresh_region):
    region = fresh_region()

    def creator(*keys):
        return [f"made-{key}" for key in keys]

    assert region.get_or_create_multi(["zulu", "alpha"], creator) == [
        "made-zulu",
        "made-alpha",
    ]


def test_get_or_create_multi_duplicate_keys_reuse_same_generated_value(fresh_region):
    region = fresh_region()

    def creator(*keys):
        return [f"generated-{key}" for key in keys]

    assert region.get_or_create_multi(["b", "a", "b"], creator) == [
        "generated-b",
        "generated-a",
        "generated-b",
    ]


def test_null_backend_never_stores_values():
    backend = NullBackend({})
    backend.set("n", CachedValue("value", {"ct": time.time(), "v": 2}))
    assert backend.get("n") is NO_VALUE
    assert backend.get_multi(["n", "m"]) == [NO_VALUE, NO_VALUE]


def test_memory_backend_basic_mapping_contract():
    backend = MemoryBackend({"cache_dict": {}})
    stored = CachedValue("v1", {"ct": time.time(), "v": 2})
    backend.set("mk", stored)
    assert backend.get("mk") is stored
    backend.delete("mk")
    assert backend.get("mk") is NO_VALUE


def test_function_key_generator_uses_module_function_namespace_and_positional_values():
    def sample(left, right):
        return left + right

    generator = function_key_generator("maths", sample)
    assert generator(3, 8) == f"{sample.__module__}:sample|maths|3 8"


def test_function_key_generator_rejects_keyword_arguments():
    def sample(left, right):
        return left + right

    generator = function_key_generator(None, sample)
    with pytest.raises(ValueError):
        generator(1, right=2)


def test_kwarg_function_key_generator_sorts_argument_names_and_uses_defaults():
    def sample(a, b=5, c=9):
        return a + b + c

    generator = kwarg_function_key_generator("kw", sample)
    assert generator(c=3, a=1, b=2) == f"{sample.__module__}:sample|kw|1 2 3"
    assert generator(a=1, c=3) == f"{sample.__module__}:sample|kw|1 5 3"


def test_function_multi_key_generator_returns_one_key_per_argument():
    def sample(*items):
        return items

    generator = function_multi_key_generator("multi", sample)
    assert generator("red", "blue") == [
        f"{sample.__module__}:sample|multi|red",
        f"{sample.__module__}:sample|multi|blue",
    ]


def test_sha1_mangle_key_accepts_text_and_bytes():
    expected = hashlib.sha1(b"fresh-key").hexdigest()
    assert sha1_mangle_key("fresh-key") == expected
    assert sha1_mangle_key(b"fresh-key") == expected


def test_length_conditional_mangler_only_changes_long_keys():
    mangler = length_conditional_mangler(5, lambda key: "mangled:" + key)
    assert mangler("tiny") == "tiny"
    assert mangler("longer") == "mangled:longer"


def test_cache_backend_from_config_dict_filters_prefix():
    class PlainBackend(CacheBackend):
        def __init__(self, arguments):
            self.arguments = arguments

    backend = PlainBackend.from_config_dict(
        {"cache.x.alpha": "A", "cache.x.beta": "B", "other": "skip"},
        "cache.x.",
    )
    assert backend.arguments == {"alpha": "A", "beta": "B"}


def test_cache_backend_serialized_default_methods_delegate_to_plain_methods():
    class DelegatingBackend(CacheBackend):
        def __init__(self):
            self.values = {}

        def get(self, key):
            return self.values.get(key, NO_VALUE)

        def get_multi(self, keys):
            return [self.values.get(key, NO_VALUE) for key in keys]

        def set(self, key, value):
            self.values[key] = value

        def set_multi(self, mapping):
            self.values.update(mapping)

    backend = DelegatingBackend()
    backend.set_serialized("one", b"1")
    backend.set_serialized_multi({"two": b"2"})
    assert backend.get_serialized("one") == b"1"
    assert backend.get_serialized_multi(["two", "missing"]) == [b"2", NO_VALUE]


def test_lock_uses_creator_when_value_function_reports_regeneration_needed():
    mutex = threading.Lock()

    def creator():
        return "new-value", time.time()

    def value_fn():
        raise NeedRegenerationException()

    with Lock(mutex, creator, value_fn, expiretime=30) as value:
        assert value == "new-value"


def test_lock_returns_existing_value_when_it_is_not_expired():
    mutex = threading.Lock()

    def creator():
        raise AssertionError("creator must not be called")

    def value_fn():
        return "existing", time.time()

    with Lock(mutex, creator, value_fn, expiretime=30) as value:
        assert value == "existing"
