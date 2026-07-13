# Requests-Cache Specification

## Product Overview

Requests-Cache adds persistent HTTP response caching to the `requests` library. It exposes a `CachedSession` class for explicit session use and patcher functions that temporarily or globally replace `requests.Session` with a cached session. Cached entries are keyed from prepared requests, saved in a cache backend, and returned as response objects compatible with `requests.Response` plus cache metadata such as `from_cache`, `created_at`, `expires`, `is_expired`, and `cache_key`.

The covered product state is the same cached response fact viewed through several public projections: session request results, the installed requests patcher, cache backend mappings, cache inspection/filter/delete APIs, response metadata, request matching keys, expiration policy, and serialized cache persistence.

## Scope

This specification covers:

- `CachedSession` and `CacheMixin` behavior for normal `requests` methods, cache hits, cache misses, refreshes, read-only mode, and cache-disabled contexts.
- Patcher functions: `install_cache()`, `uninstall_cache()`, `enabled()`, `disabled()`, `is_installed()`, `get_cache()`, `clear()`, and `delete()`.
- Local backends: memory, SQLite, and filesystem, plus the public `BaseCache`, `BaseStorage`, `DictStorage`, `SQLiteCache`, `FileCache`, and `init_backend()` surfaces needed by those workflows.
- Request matching by URL, parameters, body, selected headers, ignored parameters, custom key functions, and `create_key()` helpers.
- Expiration values, per-request/per-URL/per-session expiration, stale handling, only-if-cached behavior, cache-control headers, and removal of expired or old responses.
- Response filtering by HTTP method, status code, URL patterns, `filter_fn`, read-only mode, and cache inspection APIs.
- Built-in serializer selection and custom serializer behavior.

This specification excludes network-service backends that require Redis, MongoDB, GridFS, DynamoDB, or Memcached services. It also excludes private helper modules, exact rich `repr()` formatting, exact log text, implementation field layout, and compatibility shims for cache files produced by pre-1.0 releases.

## Installable Surface

The package is installed as `requests_cache`.

Recommended public imports are from the top-level package:

```python
import requests_cache
from requests_cache import (
    CachedSession,
    CacheMixin,
    BaseCache,
    BaseStorage,
    DictStorage,
    SQLiteCache,
    FileCache,
    init_backend,
    install_cache,
    uninstall_cache,
    enabled,
    disabled,
    get_cache,
    is_installed,
    clear,
    delete,
    create_key,
    normalize_request,
    normalize_url,
    normalize_params,
    normalize_headers,
    normalize_body,
    CacheActions,
    CacheSettings,
    CacheDirectives,
    get_expiration_datetime,
    get_url_expiration,
    DO_NOT_CACHE,
    EXPIRE_IMMEDIATELY,
    NEVER_EXPIRE,
    DEFAULT_IGNORED_PARAMS,
    init_serializer,
    pickle_serializer,
    json_serializer,
    yaml_serializer,
    utf8_serializer,
    utf8_encoder,
    safe_pickle_serializer,
)
```

Advanced users also import from documented subpackages:

```python
from requests_cache.backends import BaseCache, BaseStorage, DictStorage, init_backend
from requests_cache.cache_keys import create_key, normalize_request, normalize_url
from requests_cache.policy import CacheActions, CacheSettings, get_expiration_datetime
from requests_cache.serializers import init_serializer
```

There is no `requests-cache` console script. `python -m requests_cache` is not a supported invocation.

## Public API

`CachedSession` and `CacheMixin` accept the same core cache settings:

```python
CachedSession(
    cache_name="http_cache",
    backend=None,
    serializer=None,
    expire_after=-1,
    urls_expire_after=None,
    cache_control=False,
    content_root_key=None,
    allowable_codes=(200,),
    allowable_methods=("GET", "HEAD"),
    always_revalidate=False,
    ignored_parameters=DEFAULT_IGNORED_PARAMS,
    match_headers=False,
    filter_fn=None,
    key_fn=None,
    read_only=False,
    stale_if_error=False,
    autoclose=True,
    **kwargs,
)
```

`backend` accepts a backend instance or one of these aliases: `"sqlite"`, `"filesystem"`, `"memory"`, `"redis"`, `"mongodb"`, `"gridfs"`, or `"dynamodb"`. In this scope, `"memory"`, `"sqlite"`, and `"filesystem"` must work without external services. Unsupported aliases must raise `ValueError` when no matching backend exists.

`CachedSession.request()` and `CachedSession.send()` must accept these cache-specific request options in addition to normal `requests` options:

```python
expire_after=None
only_if_cached=False
refresh=False
force_refresh=False
```

Response objects returned by `CachedSession` must behave like `requests.Response`. A response returned from cache must have `from_cache == True`; an origin response returned by the session must have `from_cache == False`. Origin responses written to the cache must expose `created_at`, `expires`, and `cache_key`. Cached responses read back from storage must expose `created_at`, `expires`, `cache_key`, `is_expired`, `expires_delta`, `expires_unix`, `size`, and `reset_expiration()`. When a response is not cacheable or not written, `expires` and `cache_key` must be `None`.

## Product State Model

The core state is a set of cached response entries. Each entry is keyed by normalized request data and contains response content, response headers, status, URL, request metadata, creation time, expiration time, and redirect aliases when applicable.

The public projections of this state are:

- The value returned by `CachedSession` request methods.
- The patcher projection where calls through `requests` use an installed cached session.
- The backend projection exposed through `session.cache.responses`, `session.cache.redirects`, `contains()`, `filter()`, `delete()`, `clear()`, and backend persistence files.
- The response metadata projection exposed through `from_cache`, `created_at`, `expires`, `is_expired`, `cache_key`, `expires_delta`, and `size`.
- The matching projection exposed through `create_key()` and normalized request helpers.

Cross-view invariants:

- A successful cacheable origin response returned through `CachedSession` must be visible through `session.cache.contains(url=...)` and `session.cache.responses` under the same session settings.
- A later request with the same normalized key must return the saved response with `from_cache == True` until that response is expired, explicitly refreshed, deleted, or blocked by request/cache settings.
- A response deleted through `session.cache.delete()` or top-level `requests_cache.delete()` must no longer be returned as a cache hit for the matching request.
- `session.cache.clear()` and top-level `requests_cache.clear()` must remove both response entries and redirect aliases for the active cache.
- SQLite and filesystem backends must preserve cache entries across new `CachedSession` objects using the same cache name/path and compatible serializer.
- An ignored parameter must affect both request matching and stored request/response URL redaction: two otherwise equal requests differing only in ignored values must share a cache entry, and stored URLs must replace ignored values with `REDACTED`.
- A patch installed by `install_cache()` must make `requests.Session()` return a cached session until `uninstall_cache()` restores the original session factory.
- The `disabled()` context must temporarily restore non-cached `requests` behavior and then return to the previous installed cached state after exit.

## Session Caching Behavior

`CachedSession` must be a `requests.Session` subclass. Its `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, and `options()` methods must preserve normal `requests` method semantics while routing through the cache policy.

On a cache miss, a cacheable request must be sent to the origin adapter, and the response must be saved before being returned. The returned origin response must include cache metadata and `from_cache == False`. A following equivalent request must return a cached response object with the same content, status code, headers, URL, and request metadata, with `from_cache == True`.

If `only_if_cached=True` and no usable cached response exists, the session must return a response with status code `504` and reason `Not Cached` without sending the request to the origin adapter.

If `force_refresh=True`, the session must send a new request and overwrite the existing cached response when the new response is cacheable. If `refresh=True` is used with validators or cache-control headers, the session must follow the documented revalidation path for those headers.

`CachedSession.cache_disabled()` must temporarily bypass cache reads and writes for that session. It must restore the previous disabled setting after the context exits.

`read_only=True` must allow reading existing cache entries but must not write new origin responses to the cache. A read-only cache miss must return the origin response with `from_cache == False` and must leave the backend unchanged.

`autoclose=True` must close backend connections when the session closes. `autoclose=False` must leave backend objects open for sharing with another session.

Pickling a `CachedSession` must raise `NotImplementedError`.

## Patcher Behavior

`install_cache(cache_name="http_cache", backend=None, session_factory=CachedSession, **kwargs)` must patch the global `requests.Session` factory so that new sessions use the configured cached session class. The patched session must accept the same cache settings as `CachedSession`.

`uninstall_cache()` must restore the original `requests.Session` factory. Calling it when no cache is installed must leave `requests` usable.

`is_installed()` must return `True` when `requests.Session()` currently constructs a cached session, and `False` otherwise.

`enabled(*args, **kwargs)` must be a context manager that installs a cache on entry and uninstalls it on exit. It must restore the previous uninstalled state after exit.

`disabled()` must be a context manager that uninstalls the cache on entry and restores the previously installed cache on exit. When no cache is installed before entry, it must leave requests uninstalled after exit.

`get_cache()` must return the active cache object when a cache is installed and must return `None` when no cache is installed.

Top-level `clear()` and `delete(*args, **kwargs)` must operate on the currently installed cache. If no cached session is installed, they must not corrupt the `requests` session factory.

## Backends and Persistence

`init_backend(cache_name, backend=None, **kwargs)` must return a `BaseCache` subclass. If `backend is None`, it must choose SQLite when SQLite support is available and memory otherwise. If `backend` is a `BaseCache` instance, it must return that instance. If `backend` is an unknown name, it must raise `ValueError` listing the accepted aliases.

`backend="memory"` must create a non-persistent in-memory `BaseCache` with `responses` and `redirects` dict-like storage.

`backend="sqlite"` or `SQLiteCache(path)` must store responses in a SQLite file. A cache name/path without an extension must use a `.sqlite` database file. A new session using the same SQLite cache path must read responses stored by a previous closed session.

`backend="filesystem"` or `FileCache(path)` must store cached responses as files under the cache directory. It must support serializers whose encoded values are bytes or text, and it must expose a file-backed dict-like response store.

`BaseCache` must expose `responses`, `redirects`, `contains()`, `get_response()`, `save_response()`, `create_key()`, `clear()`, `delete()`, `filter()`, `recreate_keys()`, and `close()`. `contains(url=...)` must check a GET request for that URL. `contains(request=...)` must use the active key settings. `delete(urls=[...])`, `delete(requests=[...])`, and `delete(keys...)` must remove matching responses and prune redirect aliases that point to deleted responses.

`filter(valid=True, expired=True, invalid=False, older_than=None)` must yield cached responses matching the requested validity and age filters. When all filter switches are false and `older_than` is absent, it must yield nothing.

## Request Matching

Cache keys must be derived from normalized prepared request data. Equivalent GET requests with query parameters in different order must use the same key. Different methods, URLs, bodies, selected headers, or non-ignored parameters must use different keys.

`ignored_parameters` must apply to query parameters, request headers, and JSON/form body parameters. Ignored values must be excluded from matching and redacted to `REDACTED` in stored cached request and response URLs/headers/bodies when those values are present.

Default ignored parameters must include common credential names such as `Authorization`, `Proxy-Authorization`, `X-API-Key`, `X-Auth-Token`, `X-API-Token`, `X-Access-Token`, `access_token`, `api_key`, and `apikey`.

`match_headers=False` must ignore request headers for cache matching except for normal `Vary` header handling. `match_headers=True` must include all request headers. `match_headers=[...]` must include only the named headers. Header names must match case-insensitively.

`content_root_key` must restrict JSON body ignored-parameter filtering to the named root object when that root exists. If the body is not valid JSON, body matching must fall back to normalized form parameters or raw body comparison without raising for ordinary request bodies.

`key_fn` must replace the default key generator when provided. The callable must receive the request and the same key-generation keyword arguments used by the default key function.

`create_key()`, `normalize_request()`, `normalize_url()`, `normalize_params()`, `normalize_headers()`, and `normalize_body()` must be available for users who implement custom matching. Invalid inputs must raise the same standard Python exceptions that follow from the requested operation; they must not silently create a key unrelated to the request.

## Expiration and Cache-Control

Expiration values must accept `None`, numbers of seconds, `datetime.timedelta`, timezone-aware or naive `datetime.datetime`, and HTTP date strings where documented for headers. `NEVER_EXPIRE` is `-1`, `EXPIRE_IMMEDIATELY` is `0`, and `DO_NOT_CACHE` is a sentinel for disabling storage for a response.

`expire_after=None` and `expire_after=NEVER_EXPIRE` must produce responses with no expiration datetime. `expire_after=EXPIRE_IMMEDIATELY` must prevent storage for ordinary responses that do not include validators. Positive numeric and `timedelta` values must expire relative to the response creation time. Absolute datetimes must be converted to UTC-aware datetimes.

Expiration decisions must prefer request-specific information over session defaults. When cache-control processing is enabled, applicable response and request cache headers take precedence. An explicit per-request `expire_after` value overrides matching `urls_expire_after` rules, and the first matching URL rule overrides the session-level `expire_after` fallback.

When two `urls_expire_after` patterns match, the first entry in the mapping must win. String patterns must match the URL without requiring the scheme and must behave like glob prefixes with recursive wildcard behavior. Compiled regular expressions must match by regex search.

`cache_control=True` must honor supported HTTP caching headers including `Cache-Control`, `Expires`, `ETag`, `Last-Modified`, and validation headers. If a response requires validation, the next request must send conditional headers and must update the cached response on a `304 Not Modified`.

`stale_if_error=True` must return an expired cached response when refreshing it raises an exception. If `stale_if_error` is a time value, the cached response must be returned only when it is within that accepted stale window. If no usable stale response exists, the original exception must be raised.

`stale_while_revalidate` must return a stale cached response immediately while sending a background refresh for a later request. If background refresh cannot be started, the current request must still return a normal response or raise according to the non-background policy.

## Filtering and Write Policy

By default, only `GET` and `HEAD` requests with status code `200` must be cached. Other methods or status codes must return the origin response and must not write a cache entry.

`allowable_methods` must define the complete set of HTTP methods eligible for storage. Method matching must be case-insensitive. `allowable_codes` must define the complete set of status codes eligible for storage.

`filter_fn(response)` must run after a response is available. If it returns `False`, the response must not remain in the cache. If a matching response was previously cached and a later response fails `filter_fn`, the existing cached entry must be deleted.

Session-level `expire_after=DO_NOT_CACHE` and `urls_expire_after` entries using `DO_NOT_CACHE` must prevent matching responses from being stored.

`cache_control=True` must prevent storage when response headers require no-store/no-cache behavior according to the supported cache-control policy. Unsupported or malformed cache headers must not make unrelated cache entries unusable.

## Cache Inspection and Mutation

`session.cache.responses` must behave like a mutable mapping from cache keys to cached response objects. `session.cache.redirects` must behave like a mapping from redirect request keys to final response keys.

`session.cache.contains(key=...)`, `contains(request=...)`, and `contains(url=...)` must return whether the corresponding response or redirect alias exists.

`session.cache.delete()` must accept cache keys, `urls`, `requests`, `expired=True`, `invalid=True`, and `older_than=...`. It must ignore missing keys. It must remove redirect aliases that no longer point to existing responses.

`session.cache.filter()` must yield response objects that match validity, expiration, invalid-entry, and age filters. `older_than` must compare against `response.created_at`.

`CachedResponse.reset_expiration(expire_after)` must update the response expiration and return whether the response is expired after the update.

`CachedResponse.size` must return the length in bytes of the cached body content. `CachedResponse.next` must return the next prepared request in a redirect chain when one exists, otherwise `None`.

## Serializers

The `serializer` setting must accept `None`, a built-in serializer name, or a compatible custom serializer. Built-in names must include `pickle`, `json`, `yaml`, and `bson` when their dependencies are installed. Unsupported serializer names must raise a clear exception instead of silently falling back.

A custom serializer must encode cached values for storage and decode them back into equivalent response objects. The internal composition API used for encoding and decoding is not prescribed.

When a serializer produces text, filesystem storage must write text-compatible files. When a serializer produces bytes, storage must write binary-compatible files. Deserialization failures for existing cache entries must be handled as invalid cache entries during filtering or retrieval, not as successful cache hits.

## Error Semantics

`init_backend()` must raise `ValueError` for an unknown backend alias.

`CachedSession.__getstate__()` must raise `NotImplementedError`.

`get_expiration_datetime()` must raise `ValueError` for an invalid HTTP date string unless invalid-date tolerance is explicitly requested by the caller.

`only_if_cached=True` on a cache miss must return a 504 response and must not raise a network exception caused solely by the missing cache entry.

If an origin request raises and no usable stale response is permitted, the original exception must be raised.

If optional backend or serializer dependencies are missing, constructing the corresponding optional class or serializer must raise an import-related error that names the missing dependency. Local memory, SQLite, filesystem, pickle, JSON, and UTF-8 behavior must not require those optional service dependencies.

## Cross-View Invariants

- A response cached through `CachedSession.get()` must be discoverable through `session.cache.contains(url=...)` and must be returned by a later equivalent `get()` as `from_cache == True`.
- A response stored by a SQLite session must be returned from cache by a later SQLite session using the same cache path after the first session is closed.
- A response stored by a filesystem session must create a backend-visible file entry and must be returned from cache by a later filesystem session using the same cache directory and serializer.
- Calling `session.cache.delete(urls=[url])` must make the next equivalent session request miss the cache and contact the origin adapter.
- Calling `session.cache.clear()` must make every previously cached URL miss until it is requested and stored again.
- Installing the patcher must make ordinary `requests.get()` and a new `requests.Session()` use the active cache; uninstalling it must restore ordinary requests behavior.
- Entering `requests_cache.disabled()` while a patch is installed must prevent cache hits and writes inside the context and must restore the installed cache after the context exits.
- Changing `ignored_parameters` must change both key generation and stored redaction, so inspection of stored responses must agree with future cache-hit behavior.
- Expiration metadata visible on a returned response must agree with whether future requests treat it as fresh, stale, or uncacheable.
- `BaseCache.recreate_keys()` must keep existing cached responses reachable under keys recomputed with the current matching settings.

## Representative Workflows

### Session Cache Hit

```python
from requests_cache import CachedSession

session = CachedSession(backend="memory", expire_after=60)
first = session.get("https://example.test/data")
second = session.get("https://example.test/data")

assert first.from_cache is False
assert second.from_cache is True
assert second.text == first.text
```

The first cacheable request must contact the configured adapter and write a cache entry. The second equivalent request must read the entry and return a cached response. If the response is deleted, expired, refreshed, or rejected by settings, the next request must follow the corresponding miss or refresh behavior instead.

### Patching Requests

```python
import requests
import requests_cache

with requests_cache.enabled(backend="memory", expire_after=60):
    first = requests.get("https://example.test/data")
    second = requests.get("https://example.test/data")

assert requests_cache.is_installed() is False
```

Inside the context, ordinary requests calls must use the configured cache. After the context exits, the previous requests session factory must be restored.

### Persistent Local Cache

```python
from requests_cache import CachedSession

session = CachedSession("http_cache", backend="sqlite")
session.get("https://example.test/data")
session.close()

later = CachedSession("http_cache", backend="sqlite")
cached = later.get("https://example.test/data")
assert cached.from_cache is True
```

A persistent local backend must save enough response and request metadata for a later session to return the cached response without contacting the origin adapter.

## Non-Goals

- Implementing Redis, MongoDB, GridFS, DynamoDB, or other service-backed storage without the corresponding external service.
- Preserving exact private helper functions, private attributes, private module layout, or exact rich/text representation strings.
- Reproducing historical migration compatibility for cache files written by versions before 1.0.
- Reproducing internal logging messages or warning wording exactly.
- Providing a command-line interface.
- Supporting unsupported serializer dependency combinations silently.

## Invocation Protocol

There is no console script for this package. `python -m requests_cache` is not supported.

Programmatic use is through Python imports and normal `requests` adapters. Tests will instantiate sessions, mount mock adapters, call public APIs, inspect public cache mappings, and use local temporary cache paths.

Exit code behavior is not applicable because the covered surface is a Python library interface.

## Evaluation Notes

Implementations are exercised through public Python APIs. The checks cover local cache hit/miss behavior, patcher state, cache persistence, expiration priority, request matching, filtering, inspection, deletion, serializers, response metadata, and error semantics. Tests use local mock adapters and temporary files instead of live network services. Scoring focuses on observable behavior from the public contract above, not private data structures or exact textual representations.
