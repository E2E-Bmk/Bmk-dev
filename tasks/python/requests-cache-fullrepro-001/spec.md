<!-- SPEC.md -->
# Requests Cache v1 public specification draft A

## Authority and status

This pre-freeze draft is the sole public behavioral authority for
`requests-cache-fullrepro-001`. It is grounded in pinned Requests Cache 1.3.3
source commit `2cdd81a3d71319fee175ecab47c550c7e2395dda`, tree
`5919817e4d01d9f5fb4662bc2375affa53c90717`, and the independently installed
reference runtime. The intake specification, intake clauses, original oracle,
source, prefetch records, and semantic notes are design evidence only. They do
not add requirements to this document.

The normative requirements are exactly the 60 identified clauses in the seven
tables below. Explanatory prose, examples, headings, and test-design guidance
are non-normative. A later gate must map one independently runnable root to
each clause, with no additional score-bearing behavior.

## Product boundary

The product is a Python package named `requests_cache`. It augments Requests
with explicit cached sessions, local memory/SQLite/filesystem backends,
request normalization and key construction, expiration and write policy,
serializer pipelines, cached-response metadata, and reversible global Requests
patching.

All conformance observations must use documented public imports and ordinary
Python, Requests, local adapter, temporary-file, thread/event, and subprocess
facilities. A local adapter may stand in for an origin server. A subprocess may
be used to prove that persistent state, rather than process memory, carries a
response across process boundaries.

For this specification:

- an **origin call** is an invocation of the mounted local Requests adapter;
- an **equivalent request** is one whose public cache key is equal under the
  active matching settings;
- a **written origin response** is the response returned by the session after
  a cacheable origin call has been saved;
- a **cached response** is a response reconstructed from a backend entry;
- a **fresh** response has no expiration or has an expiration later than the
  current UTC time; and
- a **redirect alias** maps the prepared request for a redirecting URL to the
  final cached response key.

Tests may compare time values with a documented tolerance sufficient for call
overhead. They may use explicit events and bounded public-state polling for the
background-refresh clause. They must not use an unbounded wait or assume a
particular thread identifier, scheduling order, database schema, or filename
hash.

## Out of scope

The following are deliberately outside the contract:

- Redis, MongoDB, GridFS, DynamoDB, or any service-backed workflow;
- success of optional YAML, BSON, or signed-pickle features when their optional
  dependencies are absent;
- private helpers, private attributes, implementation source, SQL schema,
  exact serialized bytes, filename hashes, logging, warning text, repr, or
  exception-message text;
- legacy cache migration and compatibility with files produced by older
  releases;
- live network access, a command-line entry point, or `python -m requests_cache`;
- thread safety of patcher contexts or `CachedSession.cache_disabled()`;
- wall-clock performance or a particular background-thread implementation;
- an exact first task/thread/process identifier or exact filesystem metadata;
- the local-time interpretation of a naive `datetime`;
- lowercase values in `allowable_methods` (roots use Requests' prepared,
  uppercase method names); and
- cache metadata inside a response hook dispatched by Requests for the first
  raw origin response. Clause `RC-SESSION-006` covers the valid cached-response
  hook boundary after the cache has first been primed.

## Public import surface

Clause `RC-PUB-001` owns this complete top-level import list:

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
    CachedResponse,
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

The same public objects must be available through these documented advanced
imports where named:

```python
from requests_cache.backends import BaseCache, BaseStorage, DictStorage, init_backend
from requests_cache.cache_keys import create_key, normalize_request, normalize_url
from requests_cache.policy import CacheActions, CacheSettings, get_expiration_datetime
from requests_cache.serializers import init_serializer
```

`pickle_serializer`, `json_serializer`, and `utf8_serializer` are configured
serializer objects, and `utf8_encoder` is a serializer stage. `yaml_serializer`
and `safe_pickle_serializer` may instead be dependency-error providers when
their optional packages are unavailable. No clause requires these exported
providers to be functions merely because the intake catalog called them
factories.

## Atomic clauses: public local contracts

| Clause | Normative requirement |
| --- | --- |
| `RC-PUB-001` | Every top-level and advanced import listed above resolves. The eleven named class surfaces (`CachedSession`, `CacheMixin`, `BaseCache`, `BaseStorage`, `DictStorage`, `SQLiteCache`, `FileCache`, `CachedResponse`, `CacheActions`, `CacheSettings`, and `CacheDirectives`) are classes, and `CachedSession` is a subclass of `requests.Session`. Constants satisfy `NEVER_EXPIRE == -1`, `EXPIRE_IMMEDIATELY == 0`, and `DO_NOT_CACHE` is distinct from both. |
| `RC-KEY-001` | `create_key(request, ...)` returns a deterministic string. Equivalent GET requests whose query pairs differ only in order have the same key. Changing the prepared method, normalized URL, non-ignored body, selected header, `verify` value, or serializer identity changes the key for the controlled inputs used by the root. |
| `RC-KEY-002` | `normalize_request()` accepts a `requests.Request` or `PreparedRequest`, returns a prepared request copy, uppercases its method, and applies URL, header, and body normalization without mutating the caller's prepared request. |
| `RC-KEY-003` | `normalize_url(url, ignored_parameters)` normalizes scheme/host/default-port variations, sorts query pairs, and replaces each present ignored query value with the literal `REDACTED`. |
| `RC-KEY-004` | `normalize_params(value, ignored_parameters=None)` accepts text or bytes, orders parsed key/value pairs deterministically, preserves repeated and key-only parameters, and replaces present ignored values with `REDACTED`. |
| `RC-KEY-005` | `normalize_headers(headers, ignored_parameters=None)` returns a case-insensitive mapping, preserves ordinary header lookup, deterministically normalizes comma-separated multi-values, and replaces the value of an exactly named ignored header with `REDACTED`. |
| `RC-KEY-006` | `normalize_body(prepared_request, ignored_parameters, content_root_key=None)` returns bytes. It deterministically sorts and redacts JSON or form bodies, restricts JSON redaction to the named root when that root exists, and returns ordinary invalid-JSON or unrecognized-content-type bodies without raising or inventing unrelated content. |
| `RC-EXP-001` | `get_expiration_datetime()` returns `None` for `None`, `NEVER_EXPIRE`, and `DO_NOT_CACHE`; with an explicit aware `start_time`, zero returns that start time and positive numeric or `timedelta` values return the start time plus the supplied duration. |
| `RC-EXP-002` | An aware absolute `datetime` and a valid HTTP-date string are returned as UTC-aware instants. An invalid nonnumeric HTTP-date string raises `ValueError` unless `ignore_invalid_httpdate=True`, in which case it returns `None`. No exact message is required. |
| `RC-EXP-003` | `get_url_expiration(url, mapping)` examines mapping entries in insertion order and returns the value for the first matching string pattern. String patterns ignore an optional scheme and act as recursive glob prefixes. |
| `RC-EXP-004` | Compiled regular-expression URL patterns use search semantics. A missing URL, empty mapping, or no matching pattern returns `None`. |
| `RC-BACK-001` | `init_backend(name, "memory")` returns an in-memory `BaseCache` with mutable-mapping `responses` and `redirects`. Passing an existing `BaseCache` instance as `backend` returns that same object. |
| `RC-BACK-002` | `init_backend(name, unknown_alias)` raises `ValueError`. The root asserts the type only, not alias-list order or message text. |
| `RC-BACK-003` | `SQLiteCache(path_without_suffix)` exposes a `db_path` with `.sqlite` appended. `FileCache(directory, serializer=...)` exposes that directory through `cache_dir`. Both expose response and redirect mappings and can be closed through `close()`. |
| `RC-RESP-001` | A directly constructed `CachedResponse` behaves as a `requests.Response`, has `from_cache is True`, preserves public status, URL, headers, encoding, and body content, reports byte length through `size`, and reports `next is None` when no redirect successor was supplied. |
| `RC-RESP-002` | `CachedResponse.reset_expiration(value)` updates `expires` and returns the resulting `is_expired` boolean. Zero makes the response expired, while `None` or `NEVER_EXPIRE` clears expiration and makes it non-expired. `expires_delta` and `expires_unix` agree with a non-null expiration within normal rounding tolerance. |
| `RC-RESP-003` | Normal inherited Requests projections remain usable on a cached response: `content`, `text`, `json()`, `ok`, boolean truth, and `raise_for_status()` follow `requests.Response` semantics for controlled success and error inputs. |
| `RC-SER-001` | `init_serializer(None, decode_content=...)` returns `None`. `init_serializer("pickle", ...)` and `init_serializer("json", ...)` return independent configured pipeline copies with the corresponding public names and binary/text modes. Passing an already configured pipeline returns a distinct compatible copy. An unknown serializer name raises `KeyError`; exact text is not required. |
| `RC-SER-002` | The public pickle and JSON serializer pipelines each round-trip a `CachedResponse` into an equivalent `CachedResponse` preserving status, URL, headers, body, expiration, request metadata, and `from_cache`. Pickle emits bytes and JSON emits text; exact encoding is not specified. |
| `RC-SER-003` | `utf8_serializer` and `utf8_encoder` encode non-ASCII text as UTF-8 bytes and decode those bytes to the original text. If an exported optional serializer provider is unavailable, using that provider raises an import-related error naming the missing dependency; if available, this clause imposes no extra optional-format behavior. |

## Integration clauses: composed cache graph

### Session routing and response state

| Clause | Normative requirement |
| --- | --- |
| `RC-SESSION-001` | With a memory `CachedSession` and a cacheable local-adapter GET, the first request calls the adapter once, is returned with `from_cache is False`, and creates one response entry. A second equivalent request does not call the adapter, has `from_cache is True`, and preserves body, status, headers, URL, and prepared-request method/URL. The entry is simultaneously visible through `responses` and `contains(url=...)`. |
| `RC-SESSION-002` | On a miss, `only_if_cached=True` returns status `504` and reason `Not Cached` without calling the adapter or writing an entry. On an existing usable hit it returns the cached response without an origin call. The clause intentionally does not prescribe `from_cache` on the synthetic 504. |
| `RC-SESSION-003` | `force_refresh=True` bypasses a usable entry, calls the adapter, returns the new origin response with `from_cache is False`, and replaces the stored entry so the following equivalent request is a hit containing the new response. |
| `RC-SESSION-004` | `read_only=True` may serve an existing hit, but a miss or forced refresh calls the adapter without adding or replacing an entry. The returned miss is an origin response with `from_cache is False`. |
| `RC-SESSION-005` | Inside `CachedSession.cache_disabled()`, reads and writes are bypassed: an existing URL calls the adapter and does not replace its cached value, and a new URL is not stored. On exit the prior disabled state is restored and the original cached value is again returned. |
| `RC-SESSION-006` | After a URL is primed without a response hook, a later equivalent request with a normal Requests response hook invokes that hook exactly once with the cached response. The callback may observe `from_cache is True` and the cached body. No requirement applies to cache metadata in the first raw-origin hook callback. |
| `RC-SESSION-007` | A cacheable written origin response exposes `created_at`, a non-null `cache_key`, and expiration consistent with its policy. Its cached successor exposes the same key plus `is_expired`, `expires_delta`, `expires_unix`, `size`, and `reset_expiration()`. A non-written origin response has `cache_key is None` and `expires is None`. |
| `RC-SESSION-008` | Closing a session configured with `autoclose=True` invokes `close()` on its supplied public backend; `autoclose=False` does not. A backend left open can be supplied to another session and the second session can read the first session's entry. |

### Matching and redaction cross-views

| Clause | Normative requirement |
| --- | --- |
| `RC-MATCH-001` | Two GETs differing only in the value of an ignored query parameter share one entry and the second is a hit. The cached response URL and cached prepared-request URL contain `REDACTED`, not either secret value. A non-ignored query difference does not share that entry. |
| `RC-MATCH-002` | Two requests differing only in an exactly named ignored credential header share an entry. The stored request header and any same-named stored response header are redacted to `REDACTED`; unrelated headers remain observable. |
| `RC-MATCH-003` | For cacheable JSON requests and `content_root_key`, ignored fields inside the named root are redacted and excluded from value matching, while a same-named field outside that root remains part of matching. Stored request JSON agrees with those key decisions. |
| `RC-MATCH-004` | Non-ignored query values and normalized form-body values participate in keys. Controlled requests differing in either dimension call the adapter separately and remain separately addressable, while reordered equivalent form fields share an entry. |
| `RC-MATCH-005` | With `match_headers=False`, controlled header-value differences share an entry absent `Vary`. With `match_headers=True`, they separate. With a header-name list, only listed headers separate entries and the listed names are selected case-insensitively. |
| `RC-MATCH-006` | A custom `key_fn` replaces default key generation consistently for session lookup, backend storage, `contains(request=...)`, and later hits. It receives the prepared request plus the active public key settings (`ignored_parameters`, `content_root_key`, `match_headers`, serializer, and request keyword inputs such as `verify`). |

### Expiration, revalidation, and stale policy

| Clause | Normative requirement |
| --- | --- |
| `RC-POLICY-001` | `NEVER_EXPIRE` stores a reusable entry with no expiration. `EXPIRE_IMMEDIATELY` and `DO_NOT_CACHE` do not store an ordinary validator-free response; each following request calls the adapter again and each non-written response has null cache key and expiration. |
| `RC-POLICY-002` | Effective expiration precedence is: request cache directives/per-request `expire_after`, then the first matching `urls_expire_after` rule, then session `expire_after`. Stored expiration metadata and later freshness decisions agree with the selected source. |
| `RC-POLICY-003` | Resetting a stored response to immediate expiration makes the next equivalent request call the adapter and replace the stale entry. The returned replacement and following hit expose mutually consistent fresh/expired metadata and body content. |
| `RC-POLICY-004` | With cache-control processing enabled, a stale cached response carrying `ETag` or `Last-Modified` is conditionally requested with the corresponding validation header. A local-adapter `304` causes the cached body/status/request metadata to be returned and its supported updated headers/expiration to be saved for the next hit. |
| `RC-POLICY-005` | If refresh of an expired entry raises an origin exception, `stale_if_error=True` returns the stale cached response. A duration accepts only staleness within that window. With false or an exceeded window, the identical origin exception propagates. |
| `RC-POLICY-006` | For an expired entry within an enabled `stale_while_revalidate` policy, the current call returns the stale cached response without waiting for a deliberately gated local-adapter refresh. After that refresh is released and public backend state reports completion, a later request returns the refreshed body. A duration limits acceptable staleness. |

### Filtering and write policy

| Clause | Normative requirement |
| --- | --- |
| `RC-WRITE-001` | By default, successful GET and HEAD responses are eligible for storage; POST and non-200 responses are returned from the origin but not stored. Each assertion is made from a fresh controlled key so prior state cannot mask write eligibility. |
| `RC-WRITE-002` | `allowable_methods` and `allowable_codes` replace the default eligible sets. Using uppercase prepared method names, a listed method/code combination is cached and an unlisted method or code is not. |
| `RC-WRITE-003` | `filter_fn(response)` runs on an origin response. A false result leaves no stored entry and the next equivalent request calls the adapter again; a true result permits ordinary storage. |
| `RC-WRITE-004` | `filter_fn` also applies to a response obtained from an existing entry or refresh. If it returns false for that response, the matching stored entry is deleted before the call returns, so the next equivalent request is a miss. |
| `RC-WRITE-005` | With cache-control processing enabled, a response with `Cache-Control: no-store` is not written. A malformed or unsupported cache directive on one response does not delete or prevent a hit for an unrelated valid entry. `no-cache` with a validator may be stored for revalidation and is not treated as synonymous with `no-store`. |

### Backend inspection, redirects, and mutation

| Clause | Normative requirement |
| --- | --- |
| `RC-MUT-001` | `BaseCache.delete()` accepts cache keys, `urls`, and prepared `requests`; each selector removes only its matching response. Missing keys are ignored. After deletion, redirect aliases whose target no longer exists are pruned. |
| `RC-MUT-002` | `BaseCache.clear()` removes every response and redirect alias. Every formerly cached URL then misses and can be stored anew without damage to backend usability. |
| `RC-MUT-003` | A local-adapter redirect chain stores the final response plus alias entries for redirecting request keys. A later request for the original URL avoids the adapter and returns the cached final response with final URL/body, redirect history, and `from_cache is True`. |
| `RC-MUT-004` | `BaseCache.filter()` yields public response objects according to `valid`, `expired`, and `older_than` using response freshness and `created_at`. When all switches are false and no age is supplied it yields nothing. The root does not require iteration order. |
| `RC-MUT-005` | After matching settings are changed, `BaseCache.recreate_keys()` moves existing responses to keys produced by the current public key function/settings. The old key is absent, the new key is present, and a later matching session request reaches the response without an origin call. |

### Local persistence, serialization, and process boundaries

| Clause | Normative requirement |
| --- | --- |
| `RC-PERSIST-001` | A SQLite session writes a complete cached response, closes, and a new session using the same path returns an equivalent hit without calling its mounted failing adapter. Public status, URL, headers, body, request metadata, cache key, and expiration survive. |
| `RC-PERSIST-002` | A response written to SQLite in one process is returned from the same cache path in a separate process without an origin call. The child reports the expected public response fields and `from_cache is True`; process exit and output are bounded and validated. |
| `RC-PERSIST-003` | A filesystem backend with the JSON serializer creates a backend-visible text file and a later session using the same directory/serializer returns an equivalent hit. The root may verify that the public cache path is decodable text, but not exact JSON layout or filename. |
| `RC-PERSIST-004` | A filesystem backend with the pickle serializer carries a response across a real process boundary and returns an equivalent hit without an origin call. The cache artifact is binary-capable, but exact pickle bytes and filename are not specified. |
| `RC-PERSIST-005` | If a publicly enumerated filesystem response artifact is replaced with data that the active serializer cannot decode, retrieval does not produce a successful cache hit. `filter(valid=False, expired=False, invalid=True)` exposes an invalid placeholder carrying that cache key, and deletion of invalid entries restores normal backend use. |

### Global Requests patch lifecycle

| Clause | Normative requirement |
| --- | --- |
| `RC-PATCH-001` | From an uninstalled state, `install_cache()` makes `is_installed()` true, makes new `requests.Session()` objects cached sessions, and makes ordinary `requests.get()` calls share the installed backend. `get_cache()` returns that backend. `uninstall_cache()` restores the exact prior Requests session factory and makes `get_cache()` return `None`. |
| `RC-PATCH-002` | From an uninstalled state, `enabled(...)` installs a cache for its body, ordinary Requests calls demonstrate miss then hit through a root-owned local session factory, and normal or exceptional exit restores the prior uninstalled factory. |
| `RC-PATCH-003` | From an installed state, `disabled()` restores ordinary Requests sessions for its body and does not read or write the installed backend. On normal or exceptional exit it restores the exact previously installed factory and its existing cache remains usable. From an initially uninstalled state it remains uninstalled. |
| `RC-PATCH-004` | Top-level `clear()` operates on the active installed backend: after two ordinary URLs are cached, it removes both responses and redirects, and the next ordinary request for either URL calls the origin again. Calling it while uninstalled leaves Requests usable. |
| `RC-PATCH-005` | Top-level `delete()` forwards public deletion selectors to the active installed backend: deleting one cached URL makes only that URL miss while an unrelated URL remains a hit. Calling it while uninstalled leaves the Requests factory unchanged. |

## Error and cleanup rules

Every root owns all state it creates. Sessions and backends are closed; patcher
state is restored in `finally`; background refreshes and local adapter gates
have finite bounds; subprocesses have finite timeouts; and temporary paths are
root-local. An expected candidate exception is asserted by public exception
type or object identity where a clause says so, never by exact message.

An implementation may use any internal architecture. Passing behavior cannot
depend on being implemented with a particular dictionary, serializer library,
database schema, lock, worker type, or Requests wrapper. Conversely, an
implementation that satisfies only a direct helper while breaking the
cross-view outcome named by an Integration clause does not satisfy that
clause.
