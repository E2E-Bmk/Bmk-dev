# Requests-Cache Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Requests-Cache adds persistent HTTP response caching to the `requests` library. It exposes a `CachedSession` class for explicit session use and patcher functions that temporarily or globally replace `requests.Session` with a cached session. Cached entries are keyed from prepared requests, saved in a cache backend, and returned as response objects compatible with `requests.Response` plus cache metadata such as `from_cache`, `created_at`, `expires`, `is_expired`, and `cache_key`.

## Non-Goals

- Service-backed storage without the corresponding external service is excluded.
- Private helper functions, private attributes, private module layout, and exact rich or text representation strings are not specified.
- Compatibility shims for legacy cache file formats are excluded.
- Exact internal logging messages or warning wording are not part of the contract.
- Command-line interfaces are excluded.
- Unsupported serializer dependency combinations must fail clearly rather than silently fall back.

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

## Session Caching Behavior

`CachedSession` is a `requests.Session` subclass whose HTTP methods route every request through a cache policy before reaching the origin adapter. Normal `requests` semantics must be preserved, including response hooks registered via `hooks={"response": ...}`.

**Cache miss and hit.** When a cacheable request has no matching entry, the session must send the request to the origin adapter, save the response, and return it with `from_cache == False`. A subsequent equivalent request must return a cached copy with `from_cache == True` and the same content, status code, headers, URL, and request metadata.

**Response metadata.** Origin responses written to the cache must expose `created_at`, `expires`, and `cache_key`. Cached responses read from storage must additionally expose `is_expired`, `expires_delta`, `expires_unix`, `size`, and `reset_expiration()`. When a response is not cacheable or not written, `expires` and `cache_key` must be `None`.

**Per-request overrides.** `CachedSession.request()` and `CachedSession.send()` accept cache-specific options alongside normal `requests` arguments:

- When `only_if_cached=True` and no usable cached response exists, the session must return a response with status code `504` and reason `Not Cached` without contacting the origin adapter.
- When `force_refresh=True`, the session must send a new request and overwrite the existing entry if the new response is cacheable.
- When `refresh=True` is combined with validators or cache-control headers, the session must follow the documented revalidation path.

**Session-level modes.** `CachedSession.cache_disabled()` must temporarily bypass cache reads and writes for that session and restore the previous setting on exit. `read_only=True` must allow reading existing cache entries but must not write new origin responses; a read-only miss returns the origin response with `from_cache == False` and leaves the backend unchanged. `autoclose=True` must close backend connections when the session closes; `autoclose=False` must leave backend objects open for sharing.

**Restriction.** Pickling a `CachedSession` must raise `NotImplementedError`.

## Patcher Behavior

The patcher functions control whether ordinary `requests.Session()` calls produce cached sessions.

`install_cache(cache_name="http_cache", backend=None, session_factory=CachedSession, **kwargs)` must patch the global `requests.Session` factory so that new sessions use the configured cached session class.

`uninstall_cache()` must restore the original `requests.Session` factory. Calling it when no cache is installed must leave `requests` usable.

`is_installed()` must return `True` when `requests.Session()` currently constructs a cached session, and `False` otherwise.

`enabled(*args, **kwargs)` must be a context manager that installs a cache on entry and uninstalls it on exit, restoring the previous uninstalled state.

`disabled()` must be a context manager that uninstalls the cache on entry and restores the previously installed cache on exit. When no cache is installed before entry, it must leave requests uninstalled after exit.

`get_cache()` must return the active cache object when a cache is installed and `None` otherwise.

Top-level `clear()` and `delete(*args, **kwargs)` must operate on the currently installed cache. If no cached session is installed, they must not corrupt the `requests` session factory.

## Backends and Persistence

Backends store cached responses and redirect aliases. `init_backend(cache_name, backend=None, **kwargs)` must return a `BaseCache` subclass. When `backend is None`, it must choose SQLite if available, otherwise memory. When `backend` is a `BaseCache` instance, it must return that instance. When `backend` is an unknown name, it must raise `ValueError` listing the accepted aliases.

**Memory.** `backend="memory"` must create a non-persistent `BaseCache` with dict-like `responses` and `redirects` storage.

**SQLite.** `backend="sqlite"` or `SQLiteCache(path)` must store responses in a SQLite file. A cache name without an extension must produce a `.sqlite` database file; `session.cache.db_path` must reflect this resolved path. A new session using the same path must read responses stored by a previous closed session.

**Filesystem.** `backend="filesystem"` or `FileCache(path)` must store cached responses as files under the cache directory. It must support serializers whose encoded values are bytes or text and must expose a file-backed dict-like response store.

**Backend mapping interface.** `BaseCache` must expose `responses`, `redirects`, `contains()`, `get_response()`, `save_response()`, `create_key()`, `clear()`, `delete()`, `filter()`, `recreate_keys()`, and `close()`. `contains(url=...)` must check a GET request for that URL. `contains(request=...)` must use the active key settings. `delete(urls=[...])`, `delete(requests=[...])`, and `delete(keys...)` must remove matching responses and prune redirect aliases that point to deleted responses. Deleting a missing key must be silently ignored.

**Backend filtering.** `filter(valid=True, expired=True, invalid=False, older_than=None)` must yield cached responses matching the requested validity and age filters. When all filter switches are false and `older_than` is absent, it must yield nothing.

**Redirect aliases.** When the origin server returns a redirect chain, the session must store the final response and create redirect aliases so that requesting the original URL returns the cached final response with `from_cache == True` and the final URL.

## Request Matching

Cache keys control when two requests share a cached entry.

**Key generation.** Keys must be derived from normalized prepared request data. Equivalent GET requests with query parameters in different order must produce the same key. Different methods, URLs, bodies, selected headers, or non-ignored parameters must produce different keys.

**Ignored parameters.** `ignored_parameters` must apply to query parameters, request headers, and JSON/form body parameters. Ignored values must be excluded from matching and redacted to `REDACTED` in stored cached request and response URLs/headers/bodies. Default ignored parameters must include common credential names such as `Authorization`, `Proxy-Authorization`, `X-API-Key`, `X-Auth-Token`, `X-API-Token`, `X-Access-Token`, `access_token`, `api_key`, and `apikey`.

**Header matching.** `match_headers=False` must ignore request headers for cache matching except for `Vary` header handling. `match_headers=True` must include all request headers. `match_headers=[...]` must include only the named headers, matching case-insensitively.

**Body and content root.** `content_root_key` must restrict JSON body ignored-parameter filtering to the named root object when it exists. If the body is not valid JSON, body matching must fall back to normalized form parameters or raw body comparison without raising.

**Custom key function.** `key_fn` must replace the default key generator when provided. The callable must receive the request and the same key-generation keyword arguments used by the default key function.

**Normalization helpers.** `create_key()`, `normalize_request()`, `normalize_url()`, `normalize_params()`, `normalize_headers()`, and `normalize_body()` must be available for custom matching. Invalid inputs must raise normal Python exceptions; they must not silently create a key unrelated to the request.

## Expiration and Cache-Control

Expiration policies determine when cached responses become stale.

**Expiration values.** Values must accept `None`, numbers of seconds, `datetime.timedelta`, timezone-aware or naive `datetime.datetime`, and HTTP date strings. `NEVER_EXPIRE` is `-1`, `EXPIRE_IMMEDIATELY` is `0`, and `DO_NOT_CACHE` is a sentinel for disabling storage. `expire_after=None` and `NEVER_EXPIRE` must produce responses with no expiration datetime. `EXPIRE_IMMEDIATELY` must prevent storage for ordinary responses that do not include validators. Positive values must expire relative to the response creation time. Absolute datetimes must be converted to UTC-aware datetimes.

**Priority chain.** Expiration decisions must follow this precedence (highest first): response/request cache-control headers (when `cache_control=True`), explicit per-request `expire_after`, matching `urls_expire_after` rule, session-level `expire_after` fallback.

**URL-specific rules.** When two `urls_expire_after` patterns match, the first mapping entry must win. String patterns must match the URL without requiring the scheme and must behave as glob prefixes with recursive wildcard behavior. Compiled regular expressions must match by regex search.

**Cache-control headers.** `cache_control=True` must honor `Cache-Control`, `Expires`, `ETag`, `Last-Modified`, and validation headers. When a response requires validation, the next request must send conditional headers and must update the cached response on a `304 Not Modified`.

**Stale responses.** `stale_if_error=True` must return an expired cached response when refreshing raises an exception. If `stale_if_error` is a time value, the stale window must be respected. If no usable stale response exists, the original exception must be raised. `stale_while_revalidate` must return a stale response immediately while scheduling a background refresh.

## Filtering and Write Policy

By default, only `GET` and `HEAD` requests with status code `200` must be cached. Other methods or status codes must return the origin response without writing a cache entry.

`allowable_methods` must define the complete set of eligible HTTP methods (case-insensitive). `allowable_codes` must define the complete set of eligible status codes.

`filter_fn(response)` must run after a response is available. When it returns `False`, the response must not be stored. When a previously cached response exists and a refreshed response fails `filter_fn`, the existing entry must be deleted.

`expire_after=DO_NOT_CACHE` at session or URL-rule level must prevent matching responses from being stored.

`cache_control=True` must prevent storage when response headers require no-store/no-cache behavior. Unsupported or malformed cache headers must not make unrelated entries unusable.

## Cache Inspection and Mutation

The cache backend exposes its state through mapping and query interfaces.

`session.cache.responses` must behave like a mutable mapping from cache keys to cached response objects. `session.cache.redirects` must map redirect request keys to final response keys.

`session.cache.contains(key=...)`, `contains(request=...)`, and `contains(url=...)` must return whether the corresponding response or redirect alias exists.

`session.cache.delete()` must accept cache keys, `urls`, `requests`, `expired=True`, `invalid=True`, and `older_than=...`. It must ignore missing keys and must remove redirect aliases that no longer point to existing responses.

`session.cache.filter()` must yield response objects matching validity, expiration, invalid-entry, and age filters. `older_than` must compare against `response.created_at`.

`CachedResponse.reset_expiration(expire_after)` must update the response expiration and return whether the response is expired after the update.

`CachedResponse.size` must return the length in bytes of the cached body content. `CachedResponse.next` must return the next prepared request in a redirect chain, or `None`.

## Serializers

Serializers control how cached responses are encoded for storage and decoded on retrieval.

The `serializer` setting must accept `None`, a built-in name, or a compatible custom serializer. Built-in names must include `pickle`, `json`, `yaml`, and `bson` when their dependencies are installed. Unsupported names must raise a clear exception.

A custom serializer must encode cached values for storage and decode them back into equivalent response objects. When a serializer produces text, filesystem storage must write text-compatible files. When it produces bytes, storage must write binary files.

Deserialization failures for existing entries must be handled as invalid cache entries during filtering or retrieval, not as successful cache hits.

## State Model

The core state is a set of cached response entries. Each entry is keyed by normalized request data and contains response content, response headers, status, URL, request metadata, creation time, expiration time, and redirect aliases when applicable.

The public projections of this state are:

- The value returned by `CachedSession` request methods.
- The patcher projection where calls through `requests` use an installed cached session.
- The backend projection exposed through `session.cache.responses`, `session.cache.redirects`, `contains()`, `filter()`, `delete()`, `clear()`, and backend persistence files.
- The response metadata projection exposed through `from_cache`, `created_at`, `expires`, `is_expired`, `cache_key`, `expires_delta`, and `size`.
- The matching projection exposed through `create_key()` and normalized request helpers.

## Error Semantics

- When `backend` is an unknown alias, `init_backend()` must raise `ValueError`.
- When an HTTP date string is invalid, `get_expiration_datetime()` must raise `ValueError`.
- When `only_if_cached=True` and no cached response exists, the session must return a 504 response without raising a network exception.
- When an origin request raises and no usable stale response is permitted, the original exception must be raised.
- When optional backend or serializer dependencies are missing, constructing the corresponding class must raise an import-related error naming the missing dependency.
- When a `CachedSession` is pickled, it must raise `NotImplementedError`.

## Cross-View Invariants

1. A response cached through `CachedSession.get()` must be discoverable through `session.cache.contains(url=...)` and must be returned by a later equivalent `get()` as `from_cache == True`.
2. A response stored by a SQLite session must be returned from cache by a later SQLite session using the same cache path after the first session is closed.
3. A response stored by a filesystem session must create a backend-visible file entry and must be returned from cache by a later filesystem session using the same cache directory and serializer.
4. Calling `session.cache.delete(urls=[url])` must make the next equivalent session request miss the cache and contact the origin adapter.
5. Calling `session.cache.clear()` must make every previously cached URL miss until it is requested and stored again.
6. Installing the patcher must make ordinary `requests.get()` and a new `requests.Session()` use the active cache; uninstalling it must restore ordinary requests behavior.
7. Entering `requests_cache.disabled()` while a patch is installed must prevent cache hits and writes inside the context and must restore the installed cache after the context exits.
8. Changing `ignored_parameters` must change both key generation and stored redaction, so inspection of stored responses must agree with future cache-hit behavior.
9. Expiration metadata visible on a returned response must agree with whether future requests treat it as fresh, stale, or uncacheable.
10. `BaseCache.recreate_keys()` must keep existing cached responses reachable under keys recomputed with the current matching settings.

## Public Interface

### Import Surface

The package is installed as `requests_cache`.

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

### API Catalog

| Name | Kind | Role |
|------|------|------|
| CachedSession | class | requests.Session subclass with caching |
| CacheMixin | class | Mixin adding cache behavior to a session class |
| BaseCache | class | Base class for cache backends |
| BaseStorage | class | Base storage abstraction for cache entries |
| DictStorage | class | Dict-like storage helper |
| SQLiteCache | class | SQLite-backed cache backend |
| FileCache | class | Filesystem-backed cache backend |
| CachedResponse | class | Response object with cache metadata |
| CacheActions | class | Per-request cache action decisions |
| CacheSettings | class | Session-level cache settings object |
| CacheDirectives | class | Parsed cache-control directives |
| init_backend | function | Construct a cache backend from name or instance |
| install_cache | function | Monkey-patch requests.Session globally |
| uninstall_cache | function | Restore the original requests.Session factory |
| enabled | contextmanager | Temporarily install a global cache patch |
| disabled | contextmanager | Temporarily disable an installed cache patch |
| get_cache | function | Return the active installed cache object |
| is_installed | function | Report whether a cache patch is installed |
| clear | function | Clear the currently installed cache |
| delete | function | Delete entries from the currently installed cache |
| create_key | function | Generate a cache key from a request |
| normalize_request | function | Normalize a request for matching |
| normalize_url | function | Normalize a URL for matching |
| normalize_params | function | Normalize query or form parameters |
| normalize_headers | function | Normalize request headers for matching |
| normalize_body | function | Normalize request body for matching |
| get_expiration_datetime | function | Parse expiration values into datetimes |
| get_url_expiration | function | Resolve expiration for a URL against rules |
| init_serializer | function | Construct a serializer from name or object |
| pickle_serializer | function | Pickle-based serializer factory |
| json_serializer | function | JSON-based serializer factory |
| yaml_serializer | function | YAML-based serializer factory |
| utf8_serializer | function | UTF-8 text serializer factory |
| utf8_encoder | function | UTF-8 encoding helper for serializers |
| safe_pickle_serializer | function | Restricted pickle serializer factory |
| NEVER_EXPIRE | constant | Sentinel for no-expiration policy |
| EXPIRE_IMMEDIATELY | constant | Sentinel for immediate-expiration policy |
| DO_NOT_CACHE | constant | Sentinel for disabling storage |
| DEFAULT_IGNORED_PARAMS | constant | Default credential-like parameters to ignore |

### CLI Entry Points

There is no console script for this package. `python -m requests_cache` is not supported. Programmatic use is through Python imports and normal `requests` adapters.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. The memory, SQLite, filesystem, JSON, and pickle workflows must operate with local files and adapters without requiring network services.

## Appendix B: Assessment Notes

Implementations are exercised through public Python APIs. The checks cover local cache hit/miss behavior, patcher state, cache persistence, expiration priority, request matching, filtering, inspection, deletion, serializers, response metadata, and error semantics. Tests use local mock adapters and temporary files instead of live network services. The focus is on observable behavior from the public contract above, not private data structures or exact textual representations.
