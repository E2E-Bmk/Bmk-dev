# dogpile.cache Specification

═══ Context Layer ═══

## Product Overview

`dogpile.cache` is a Python caching library that organizes key/value storage behind configured cache regions, backend plugins, generated cache keys, value creation locks, and decorator helpers for caching function results. A region is the application-facing object: it is configured with a backend, optional expiration policy, optional key mangling, optional serialization, optional proxy wrappers, and optional asynchronous refresh behavior.

The package also exposes backend and lock extension points. Applications create regions with `make_region()` or `CacheRegion`, configure them with named backends, call region methods such as `get`, `set`, `delete`, and `get_or_create`, and attach caching behavior to functions with `cache_on_arguments` and `cache_multi_on_arguments`.

## Non-Goals

- This specification does not require Redis, Valkey, Memcached, Mako, or any live external cache service.
- This specification does not require multiprocessing, cross-process invalidation, distributed locking, TLS configuration, or network client behavior.
- This specification does not define private loader objects, private region attributes, internal log text, exact exception message prose, or exact `repr()` output.
- This specification does not require storage eviction, maximum-size management, automatic cleanup of expired values, or background thread management beyond the public `async_creation_runner` callback contract.
- This specification does not define compatibility modules except where the public import surface below names them.

## Scope

This specification covers the documented local cache-region API, the memory, memory-pickle, null, and DBM backends, public backend extension hooks, function-result decorators, public key-generation helpers, public proxy wrappers, serializer/deserializer integration, and the `dogpile.Lock` coordination primitive.

This specification is limited to deterministic local behavior that can be exercised through public imports in a Python process. Live Redis, Valkey, Memcached, Mako integration, network transports, private compatibility shims, and concurrency stress behavior are outside this scope.

═══ Orientation Layer ═══

## Representative Workflows

A typical region workflow creates and configures a memory-backed region, stores values directly, then uses `get_or_create` to compute missing or stale values:

```python
from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE

region = make_region().configure("dogpile.cache.memory", expiration_time=300)
region.set("user:12", {"name": "Ada"})
assert region.get("user:12") == {"name": "Ada"}
assert region.get("missing") is NO_VALUE

def load_user():
    return {"name": "Grace"}

assert region.get_or_create("user:99", load_user) == {"name": "Grace"}
```

A function-caching workflow decorates a normal callable and then uses helper methods attached to the decorated function:

```python
from dogpile.cache import make_region

region = make_region().configure("dogpile.cache.memory")

@region.cache_on_arguments(namespace="profiles")
def load_profile(user_id):
    return {"id": user_id}

load_profile(8)          # creates and caches the value
load_profile.get(8)      # reads the cached value without calling the function
load_profile.set({"id": 8, "manual": True}, 8)
load_profile.invalidate(8)
load_profile.refresh(8)  # calls the original function and stores its result
```

A backend-extension workflow registers or wraps a backend through public APIs:

```python
from dogpile.cache import make_region, register_backend
from dogpile.cache.proxy import ProxyBackend

register_backend("dictionary", "mypackage.mybackend", "DictionaryBackend")

class CountingProxy(ProxyBackend):
    def get(self, key):
        return self.proxied.get(key)

region = make_region().configure("dictionary", wrap=[CountingProxy])
```

═══ Behavior Layer ═══

## Region Configuration And Backend Selection

This section describes how cache regions are created, configured, and connected to backend implementations.

**Region construction.** The `make_region` function must return a `CacheRegion`. When `name` is provided, the region must expose that value through its public `name` attribute. A newly constructed region must report `is_configured` as false and must raise `RegionNotConfigured` when code accesses `backend` before configuration.

**Backend configuration.** When `configure` is called with a valid backend name, the region must instantiate that backend, store the backend on `backend`, report `is_configured` as true, and return the same region object. When `configure` is called twice without `replace_existing_backend`, it must raise `RegionAlreadyConfigured`. When `replace_existing_backend` is true, the region must replace the configured backend while preserving user-supplied region options such as a region-level `key_mangler`.

**Configuration values.** The `expiration_time` option accepts numbers, `None`, and `datetime.timedelta` values. When `expiration_time` is a `timedelta`, the region must store its total seconds as an integer number of seconds. If `expiration_time` is neither numeric, `None`, nor `timedelta`, then `configure` must raise `ValidationError`.

**Dictionary configuration.** When `configure_from_config` receives a mapping and a prefix, it must read the backend name from `{prefix}backend`, read optional expiration from `{prefix}expiration_time`, coerce string booleans and `None`-like values, and pass keys under `{prefix}arguments.` to the backend constructor after removing that argument prefix.

**Backend lookup.** The built-in backend names in this scope are `dogpile.cache.memory`, `dogpile.cache.memory_pickle`, `dogpile.cache.null`, and `dogpile.cache.dbm`. When `register_backend` associates a name with a module path and class name, a later region configuration using that name must load that class. If a backend name is unknown, then `configure` must raise `PluginNotFound`.

## Region Value Operations

This section defines direct key/value operations on a configured cache region.

**Missing and stored values.** The `NO_VALUE` sentinel must represent a missing cache value, must evaluate as false in boolean context, must remain distinct from `None`, and must expose a `payload` attribute that refers back to `NO_VALUE`. When `get` does not find a key, it returns `NO_VALUE`. When `set` stores a payload for a key, a later `get` for that key returns the payload, including `None` if `None` was the stored payload.

**Single-key deletion.** When `delete` is called for an existing key, the key must no longer be visible through `get`. When `delete` is called for a missing key, it must complete without raising.

**Multi-key operations.** When `set_multi` receives a mapping, the region must store each key/value pair. When `get_multi` receives a sequence of keys, it returns a list with one item per requested key in the same order as the request. Missing keys in that list must be represented by `NO_VALUE`. When `get_multi` receives an empty sequence, it returns an empty list. When `delete_multi` receives keys, it must delete existing keys and ignore missing keys.

**Metadata projection.** When `get_value_metadata` finds a live value, it returns a `CachedValue` object whose `payload` is the stored payload and whose `cached_time` is the epoch timestamp assigned at storage time. The `age` property returns elapsed seconds relative to current time. When no live value exists for the key, `get_value_metadata` returns `None`.

**Key mangling.** When a region has a `key_mangler`, every region key passed to backend-facing `get`, `get_multi`, `set`, `set_multi`, `delete`, `delete_multi`, `get_or_create`, and `get_or_create_multi` must be transformed before it reaches the backend. When no region-level mangler is supplied, a backend-provided `key_mangler` must be adopted. When a region-level mangler is supplied, it must override any backend-provided mangler.

## Expiration Invalidation And Creation

This section defines freshness, invalidation, and value generation behavior.

**Expiration on reads.** When `get` or `get_multi` is called without `ignore_expiration`, it must compare the cached value creation time to the call-specific `expiration_time` argument when provided, otherwise to the configured region expiration. If the value is stale, the method returns `NO_VALUE` for that key. When `ignore_expiration` is true, the method must return the stored payload even if expiration or region invalidation would otherwise hide it.

**Single-key creation.** When `get_or_create` finds no live value, it must call the supplied `creator`, cache the created value unless `should_cache_fn` returns false for that value, and return the created payload. When it finds a live value, it returns the existing payload without calling `creator`. When `creator_args` is supplied, the region must pass those positional and keyword arguments to the creator during generation. When the call-specific `expiration_time` is `-1`, the call treats existing values as never expiring.

**Multi-key creation.** When `get_or_create_multi` receives keys, it must preserve the caller's key order in the returned sequence. It must call the `creator` only for keys that are absent, expired, invalidated, or otherwise need regeneration, and the creator receives those keys as positional arguments. Duplicate requested keys must share the same generated or cached value. When `should_cache_fn` is supplied, it must be applied independently to each generated value.

**Invalidation.** When `invalidate` is called with hard invalidation, later `get` calls must hide older cached values unless `ignore_expiration` is true, and later `get_or_create` or `get_or_create_multi` calls must regenerate affected values. When `invalidate` is called with soft invalidation, later creation calls must require a non-`None` expiration time; otherwise they must raise `DogpileCacheException`.

**Asynchronous refresh.** When a region has an `async_creation_runner` and a stale value already exists, `get_or_create` must return the stale value immediately and call the runner with the region, original key, creator callable, and mutex. The runner is responsible for releasing the mutex. When no prior value exists, the first creation must run synchronously and must not call the asynchronous runner.

## Decorator Caching Workflows

This section defines the function decorators that use region storage and key generation.

**Single-result decorator.** The `cache_on_arguments` decorator must cache the decorated function's return value under a key derived from the function module, function name, optional `namespace`, and argument values. Repeated calls with the same cache key must return the cached value without invoking the function again. Calls with a different cache key must generate and store a distinct value.

**Decorated helper methods.** A function decorated with `cache_on_arguments` must expose `get`, `set`, `invalidate`, `refresh`, and `original` helper attributes. The `get` helper returns the cached value or `NO_VALUE` for that decorated-call key. The `set` helper stores a caller-provided value for that key. The `invalidate` helper deletes that key. The `refresh` helper calls the original function, stores the new result, and returns it. The `original` helper calls the underlying function without reading or writing the cache.

**Keyword-aware calls.** The default decorator wrapper must accept calls that are equivalent under the wrapped function signature, including keyword arguments accepted by the function. The standalone `function_key_generator` rejects keyword arguments, while `kwarg_function_key_generator` must produce the same key for equivalent positional and keyword calls and must include default argument values when arguments are omitted.

**Standalone key helpers.** `function_key_generator` must return keys containing the wrapped function module name, function name, optional namespace, and positional argument values. Its default text form uses `module:function`, then `|namespace` when a namespace is present, then `|` followed by space-separated positional argument values. `function_multi_key_generator` must return one key per supplied argument using the same module, function, and namespace prefix. `kwarg_function_key_generator` must normalize equivalent positional and keyword calls before producing the same text form. `sha1_mangle_key` must accept text or bytes and return the SHA-1 hexadecimal digest. `length_conditional_mangler` must leave keys at or below the configured length unchanged and must apply the supplied mangler to longer keys.

**Method keys.** When the default key generator sees a first function parameter named `self` or `cls`, it must ignore that instance or class argument in the generated key. Namespaces must disambiguate otherwise identical module/function/argument keys.

**Multi-result decorator.** The `cache_multi_on_arguments` decorator must cache one value per argument key. On later calls it must fetch already cached keys and call the decorated function only for missing keys. The decorated multi function must expose `get`, `set`, `invalidate`, and `refresh` helpers over multiple keys. When `asdict` is true, the decorated function returns and accepts mappings keyed by the original argument values; missing generated keys are omitted from the returned mapping unless supplied by cached data or helper `set`.

## Backend Extension Serialization And Proxies

This section defines public extension contracts for cache backends, serializer integration, and proxy wrappers.

**Backend base class.** A `CacheBackend` subclass receives an `arguments` mapping on construction. The default `from_config_dict` class method must build a new backend from only mapping keys that start with the requested prefix, stripping that prefix from argument names. Backend `delete` and `delete_multi` methods must be idempotent. Backend `get` methods return `NO_VALUE` for absent keys.

**Serialized backend methods.** The default `CacheBackend` serialized methods must delegate to the non-serialized methods: `get_serialized` to `get`, `get_serialized_multi` to `get_multi`, `set_serialized` to `set`, and `set_serialized_multi` to `set_multi`. A `BytesBackend` subclass uses the serialized methods as its primary storage interface.

**Region serialization.** When a region has a `serializer`, it must serialize only the payload portion of a `CachedValue` before passing bytes to the backend. When a region has a `deserializer`, it must reconstruct the `CachedValue` metadata and payload when reading from the backend. If the deserializer raises `CantDeserializeException`, the region treats that backend value as missing and proceeds through normal regeneration behavior.

**Built-in backend behavior.** `MemoryBackend` stores `CachedValue` objects in a supplied or internal dictionary until keys are deleted. `MemoryPickleBackend` stores serialized data so that later reads return a copy independent of mutations to the original object supplied to `set`. `NullBackend` must return `NO_VALUE` for every `get`, return one `NO_VALUE` per requested key from `get_multi`, and ignore all set and delete operations. `DBMBackend` stores serialized values in a local DBM file named by `arguments["filename"]`; values written by one region must be visible to another region configured with the same filename.

**Proxy wrappers.** A `ProxyBackend` instance or subclass in the `wrap` list must wrap the configured backend. Wrapper classes must be instantiated automatically. The final `region.backend` is the outermost proxy, each proxy's `proxied` attribute points to the next proxy or concrete backend, and `actual_backend` returns the concrete backend under the chain. Proxy methods that are not overridden must delegate to `proxied`. A proxy that changes values in `set_multi` must not mutate the mapping values that `get_or_create_multi` returns to the caller.

## Dogpile Lock Coordination

This section defines the public lock primitive used by region creation operations.

**Fresh values.** When a `Lock` context receives a value and creation time from `value_and_created_fn` and that value is not expired, entering the context must yield the existing value without calling `creator`.

**Missing values.** When `value_and_created_fn` raises `NeedRegenerationException`, entering the context must acquire the mutex, call `creator`, yield the new value portion returned by `creator`, and release the mutex before leaving the creation path.

**Stale values and asynchronous creation.** When a prior value exists but is expired and an `async_creator` is supplied, the lock must pass the mutex to `async_creator`, yield the stale value for the current context, and rely on the asynchronous creator to release the mutex. When no asynchronous creator is supplied, the lock must call the synchronous `creator` for stale values it is elected to regenerate.

═══ Contract Layer ═══

## Product State Model

The core state is a set of cached entries keyed by logical user keys after optional key mangling. Each entry contains a payload and metadata, including a creation timestamp. The public projections are region read/write methods, decorated function helper methods, backend storage methods, invalidation state, serializer/deserializer boundaries, proxy chains, DBM file persistence, and dogpile lock creation state.

A configured region must keep its backend, expiration policy, invalidation strategy, serializer/deserializer, key mangler, proxy chain, and async creation runner consistent across all public operations. Expiration and invalidation affect visibility and regeneration, but they do not by themselves delete backend data.

## Error Semantics

| Condition | Required result |
|---|---|
| Accessing `backend` on an unconfigured region | Raise `RegionNotConfigured` |
| Configuring a region twice without replacement | Raise `RegionAlreadyConfigured` |
| Unknown backend name | Raise `PluginNotFound` |
| Invalid `expiration_time` type | Raise `ValidationError` |
| Soft invalidation used by creation calls without a non-`None` expiration time | Raise `DogpileCacheException` |
| Standalone `function_key_generator` or `function_multi_key_generator` receives keyword arguments | Raise `ValueError` |
| Deserializer raises `CantDeserializeException` | Treat the backend value as missing |
| Backend subclass does not implement required abstract storage methods and those methods are called | Raise `NotImplementedError` |

## Cross-View Invariants

1. A value written through `set`, `set_multi`, decorator `set`, decorator `refresh`, or creation methods must be visible through the corresponding region, metadata, and decorator `get` projections until deleted, expired, invalidated, or rejected by `should_cache_fn`.
2. The same logical key transformation must be used by direct region methods, creation methods, decorator helpers, and backend-facing operations.
3. Expiration and invalidation must hide values from normal reads and creation checks while `ignore_expiration=True` reads must still return the stored payload.
4. A generated value returned from `get_or_create` or `get_or_create_multi` must match the value stored for later reads unless `should_cache_fn` rejects that value or a proxy deliberately transforms the backend representation.
5. Serializer and deserializer behavior must preserve user payloads across backend storage while leaving metadata available through `CachedValue`.
6. A proxy chain must preserve backend behavior for methods it does not override and must expose the same logical cached state through region operations.
7. DBM-backed regions configured with the same filename must project the same stored entries across region instances.
8. Decorator helper methods must operate on the same cache keys used by normal decorated calls.
9. The dogpile lock and region creation APIs must coordinate so that a missing value blocks for synchronous creation while a stale value with an async runner returns the old payload and schedules refresh.

═══ Reference Layer ═══

## Installable Surface

### Import Surface

```python
from dogpile import Lock, NeedRegenerationException
from dogpile.cache import CacheRegion, make_region, register_backend
from dogpile.cache import exception
from dogpile.cache.api import (
    CacheBackend,
    BytesBackend,
    CacheMutex,
    CachedValue,
    CantDeserializeException,
    NO_VALUE,
)
from dogpile.cache.backends.file import DBMBackend
from dogpile.cache.backends.memory import MemoryBackend, MemoryPickleBackend
from dogpile.cache.backends.null import NullBackend
from dogpile.cache.proxy import ProxyBackend
from dogpile.cache.util import (
    function_key_generator,
    function_multi_key_generator,
    kwarg_function_key_generator,
    length_conditional_mangler,
    sha1_mangle_key,
)
from dogpile.cache.exception import (
    DogpileCacheException,
    PluginNotFound,
    RegionAlreadyConfigured,
    RegionNotConfigured,
    ValidationError,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `CacheRegion` | class | Front-end object that binds region configuration to cache operations and decorators. |
| `make_region` | function | Constructs a `CacheRegion` with optional region-level options. |
| `register_backend` | function | Registers a backend class under a loadable backend name. |
| `NO_VALUE` | constant | Sentinel returned for cache misses. |
| `CachedValue` | class | Tuple-like value wrapper containing payload and metadata. |
| `CacheBackend` | class | Base class for object-oriented backend implementations. |
| `BytesBackend` | class | Base class for backends that store serialized bytes. |
| `CacheMutex` | class | Public mutex protocol for backend-provided creation locks. |
| `CantDeserializeException` | exception | Signal that a serialized backend value must be regenerated. |
| `ProxyBackend` | class | Backend wrapper that delegates operations to a proxied backend. |
| `MemoryBackend` | class | Dictionary-backed in-memory backend. |
| `MemoryPickleBackend` | class | Dictionary-backed backend that serializes values with pickle. |
| `NullBackend` | class | Backend that disables storage and always misses. |
| `DBMBackend` | class | Local DBM-file-backed serialized backend. |
| `function_key_generator` | function | Default single-result decorator key generator. |
| `function_multi_key_generator` | function | Default multi-result decorator key generator. |
| `kwarg_function_key_generator` | function | Key generator that accounts for keyword arguments and defaults. |
| `length_conditional_mangler` | function | Builds a key mangler that only transforms long keys. |
| `sha1_mangle_key` | function | Converts text or bytes keys into SHA-1 hex strings. |
| `Lock` | class | Dogpile coordination context manager for stale and missing values. |
| `NeedRegenerationException` | exception | Signal from a value function that no usable value exists. |
| `DogpileCacheException` | exception | Base cache-specific exception for invalid cache operations. |
| `PluginNotFound` | exception | Error for unknown backend plugins. |
| `RegionAlreadyConfigured` | exception | Error for duplicate region configuration. |
| `RegionNotConfigured` | exception | Error for using an unconfigured region. |
| `ValidationError` | exception | Error for invalid user-supplied options. |

### CLI Entry Points

There is no console script for this package. `python -m dogpile` and `python -m dogpile.cache` are not supported. Programmatic use is through Python imports.

## Invocation Protocol

The package is invoked by installing it into a Python environment and importing the public modules and symbols listed in `Installable Surface`. Users create cache regions with `make_region()` or `CacheRegion`, configure a backend with `configure` or `configure_from_config`, and then call public region, backend, decorator-helper, key-generator, proxy, and lock APIs directly from Python code. There is no supported command-line invocation.

═══ Meta Layer ═══

## Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `pytest`, `decorator`, and `stevedore`. The target package is not pre-installed. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package installs with pip.

## Evaluation Notes

The implementation is exercised through public imports only. Checks cover region configuration, value storage, cache misses, expiration, invalidation, creation functions, multi-key workflows, decorator helper methods, key generation, serializer boundaries, proxy wrapping, DBM persistence, custom backend registration, null and memory backend behavior, and dogpile lock coordination. The tests use fresh keys and values and do not depend on private modules, live services, exact message prose, or exact representation strings.
