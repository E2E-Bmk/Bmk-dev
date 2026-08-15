# VCR Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

VCR is a Python library named `vcr` that records HTTP interactions made by user code into cassette files and replays them on later runs. The package lets tests become deterministic by intercepting outgoing HTTP requests, matching them to recorded requests, and returning the previously recorded responses instead of performing network traffic.

## Non-Goals

- Third-party HTTP client ecosystems beyond the documented standard-library and requests workflows are excluded unless their behavior is specified here and the dependency is installed.
- Private implementation modules and private helper functions are not specified.
- Pytest plugin entry points are excluded; pytest integration is out of scope for this contract.
- Byte-for-byte cassette formatting is not specified; semantically equivalent serialization is sufficient.
- Live external HTTP calls during replay are excluded.

## Representative Workflows

Using a cassette as a context manager:

```python
import vcr
import urllib.request

with vcr.use_cassette("example.yaml") as cassette:
    body = urllib.request.urlopen("http://example.test/").read()
```

Required behavior:

- On first use when the cassette file does not already exist, VCR records HTTP interactions made inside the context and saves them to the cassette path.
- On later use when the cassette file exists, VCR loads recorded interactions, intercepts matching requests, and returns the recorded response without performing the real network request.
- The same cassette state must be visible through the `Cassette` object returned by the context manager.
- Leaving the context restores patched HTTP behavior so requests outside the context are not intercepted by that cassette.

Using a cassette as a decorator:

```python
@vcr.use_cassette("example.yaml")
def test_something():
    ...
```

Required behavior:

- The cassette is active for the duration of the function call.
- The decorated function receives normal arguments and return values.
- The cassette is saved and patches are restored after the function exits, subject to exception handling rules.

## VCR Configuration

The `VCR` class provides configured recording defaults that propagate to every cassette opened through it.

**Recorder defaults.** Configuration options on a `VCR` object must provide defaults for cassettes created by that object. Keyword arguments passed to `use_cassette()` must override the corresponding `VCR` defaults for that cassette. A module-level `vcr.use_cassette()` must behave like using a default `VCR` instance.

**Library directory.** When `cassette_library_dir` is set on a `VCR` object, it must be used to resolve relative cassette paths and automatic cassette names. An override `cassette_library_dir` passed to `use_cassette()` must take precedence over the `VCR`-level default.

**Default settings.** The default serializer must write YAML cassette files when PyYAML is available. The default record mode must be `once`. The default match configuration must use `["method", "scheme", "host", "port", "path", "query"]`. `serializer`, `record_mode`, `match_on`, filters, callbacks, patch settings, and cassette behavior flags must affect the cassette opened by `use_cassette()`.

## Cassette Lifecycle

Cassettes are activated through context managers or decorators and follow a consistent lifecycle of opening, recording, and saving.

**Context manager usage.** `use_cassette(path)` must work as a context manager that activates a cassette on entry and saves it on exit. The `Cassette` object must be available as the `as` target. Leaving the context must restore patched HTTP behavior so requests outside the context are not intercepted by that cassette.

**Decorator usage.** `use_cassette(path)` must also work as a decorator. The cassette must be active for the duration of the decorated function call. The decorated function must receive normal arguments and return values. The cassette must be saved and patches must be restored after the function exits, subject to exception handling rules.

**Automatic naming.** When `use_cassette` is used as a decorator without an explicit path, both `@my_vcr.use_cassette` and `@my_vcr.use_cassette()` must be valid decorator forms. The cassette path must be generated from the decorated function name. When `cassette_library_dir` is configured, the generated cassette must be placed in that directory. When `cassette_library_dir` is not configured, the cassette must be placed next to the file containing the decorated function when that location is discoverable. `path_transformer` and `func_path_generator` may customize generated paths. `VCR.ensure_suffix(".yaml")` must return a transformer that appends the requested suffix when it is not already present and must leave paths that already end with the suffix unchanged.

**Exception handling and saving.** By default, VCR must save cassette data when leaving a context even if the enclosed code raises an exception. When `record_on_exception` is `False`, VCR must not save newly recorded cassette data when the enclosed code raises an exception. Patches must still be restored when exceptions occur.

**Custom patches.** VCR supports `custom_patches`, where each patch identifies a target object, an attribute name, and a replacement value. Custom patches must be applied when a cassette context is entered and must be restored to their original values when the cassette context exits, composing with the normal cassette lifecycle.

## Record Modes

Record modes determine whether a cassette records new interactions, replays existing ones, or rejects unmatched requests.

**Mode constants.** Record modes must be accessible as constants `vcr.mode.ONCE`, `vcr.mode.NONE`, `vcr.mode.NEW_EPISODES`, and `vcr.mode.ALL`, and must also be accepted as lowercase string names `"once"`, `"none"`, `"new_episodes"`, and `"all"`.

**ONCE mode.** When `record_mode` is `ONCE` and no cassette file exists, new interactions must be recorded. When a cassette file already exists, recorded interactions must be replayed, and any new request that does not match an existing recorded interaction must raise `CannotOverwriteExistingCassetteException`.

**NONE mode.** When `record_mode` is `NONE`, no new interactions may be recorded. If a cassette file exists, recorded interactions must be replayed, and `play_count` must reflect the number of replayed interactions. Any new request that does not match an existing recorded interaction must raise `CannotOverwriteExistingCassetteException`. If no cassette file exists, every request must raise `CannotOverwriteExistingCassetteException`.

**NEW_EPISODES mode.** When `record_mode` is `NEW_EPISODES`, recorded interactions must be replayed for matching requests and new unmatched interactions must be recorded alongside existing ones. After replaying one existing interaction and recording one new interaction, `play_count` must be `1` and `len(cassette)` must include both the replayed and newly recorded interactions.

**ALL mode.** When `record_mode` is `ALL`, every request must be recorded as a new interaction. Existing recorded interactions must not be replayed; `play_count` must remain `0` after requests are made.

**Rejection behavior.** When a new request is rejected under the current record mode, the cassette must raise `CannotOverwriteExistingCassetteException`, a public VCR error that lets callers distinguish an unhandled HTTP request from normal transport failures.

## Request Representation

The `Request` object represents a normalized outgoing HTTP request and drives matching, serialization, and cassette bookkeeping.

**URI components.** A `Request` must expose `uri` containing the original request URI. `url` must be a backwards-compatible alias for `uri` and must return the same value. `scheme` must return the URI scheme in lowercase. `protocol` must be a backwards-compatible alias for `scheme`. `host` must return the hostname normalized to lowercase. `port` must return the explicit port from the URI when present; when no port is specified, it must default to `80` for HTTP and `443` for HTTPS. `path` must return the path component without the query string. `query` must return query parameters as a sorted list of `(key, value)` tuples; when the same key appears multiple times, all values must be preserved and the entire list must be sorted by key then value.

**Body and method.** `method` must return the HTTP method string. `body` must return the request body bytes, or `None` when no body was provided.

**Serialization.** Requests must be serializable into cassette files and reconstructable when a cassette is loaded. The reconstructed request must expose the same normalized URI components and body as a freshly constructed request. Header information must be available to the extent needed for documented header matching, filtering, recording, and replay.

## Request Matching

Request matching determines whether an incoming request corresponds to a previously recorded interaction in the cassette.

**Built-in matchers.** The `vcr.matchers` module must provide matchers named `method`, `uri`, `scheme`, `host`, `port`, `path`, `query`, `raw_body`, `body`, and `headers`. Each matcher must accept two `Request` objects. A successful match must return `None`. A mismatch must raise `AssertionError`. A request must match a recorded request only when all configured matchers agree. Matcher failures should produce useful mismatch information where practical.

**Component matchers.** The `method` matcher must compare HTTP methods. The `uri` matcher must compare full request URIs. The `scheme` matcher must compare normalized lowercase schemes. The `host` matcher must compare normalized lowercase hostnames. The `port` matcher must compare effective ports including protocol defaults. The `path` matcher must compare path components, ignoring scheme, host, port, and query. The `query` matcher must compare normalized sorted query parameter pairs.

**Body matchers.** The `raw_body` matcher must compare request body bytes directly. The `body` matcher must compare request bodies after unmarshalling by content type for XML-RPC, JSON, and form-urlencoded bodies, falling back to `raw_body` when unmarshalling does not apply. JSON body comparison must be semantic: equivalent JSON objects with different key ordering must match.

**Header matcher.** The `headers` matcher must compare request headers in a case-insensitive manner. A header value change must cause a mismatch even when header names differ only in case.

**Custom matchers.** `VCR.register_matcher(name, callable)` must register a custom matcher by name. After registration, callers may use the matcher name in `match_on`. A custom matcher returning `True` must indicate a match. A custom matcher returning `False` must cause the cassette to treat the request as unmatched and not replay a recorded response.

## Serialization and Persistence

Serialization controls the cassette wire format and persistence controls where cassette data is stored and loaded.

**Serializer interface.** A serializer must provide `serialize(cassette_dict)` and `deserialize(cassette_string)` methods. Built-in YAML serialization must be available when PyYAML is installed. Built-in JSON serialization must be available. `VCR.register_serializer(name, serializer)` must register a custom serializer by name. After registration, callers may use the serializer by setting `serializer=name` on a VCR object or cassette. The serializer's `deserialize` method must be called when the cassette is loaded, and its `serialize` method must be called when the cassette is saved.

**Cassette format.** The `vcr.serialize.serialize` function must project cassette requests and responses into a dict with a `version` key set to `1` and an `interactions` key containing an ordered list of request/response interaction dicts. Each interaction must contain a `request` dict with `method`, `uri`, `body`, and `headers` keys, and a `response` dict with `status`, `body`, and `headers` keys. The response `status` must contain `code` and `message` keys. The `vcr.serialize.deserialize` function must reconstruct `Request` objects and response dicts from this format, returning a `(requests, responses)` tuple. Deserialized requests must expose the same normalized URI components and body as freshly constructed requests, converting string body values to bytes.

**Filesystem persister.** The default `FilesystemPersister` must load and save cassette files. `FilesystemPersister.save_cassette(path, cassette_dict, serializer)` must create parent directories when they do not exist and must write the serialized data to the specified path. `FilesystemPersister.load_cassette(path, serializer)` must read the file, deserialize it, and return a `(requests, responses)` tuple. Loading a missing cassette file must raise `CassetteNotFoundError`. Loading malformed cassette data must raise `CassetteDecodeError`.

**Custom persisters.** `VCR.register_persister(persister)` must register a custom persister. A custom persister must provide `load_cassette` and `save_cassette` static methods. When a custom persister raises `CassetteNotFoundError` or `CassetteDecodeError` during loading, the cassette must start empty without propagating the exception. When a custom persister raises any other exception, it must propagate to the caller.

**Cassette loading.** `Cassette.load(path=...)` must load a cassette from a file using the default serializer and persister and must return a `Cassette` object whose length and contents reflect the stored interactions.

## Filtering and Ignoring

Filters control which parts of requests and responses are stored in cassettes, and ignore rules exempt entire requests from VCR interception.

**Data filters.** `filter_headers`, `filter_query_parameters`, and `filter_post_data_parameters` must accept simple key names or `(key, replacement)` pairs. A replacement may be a static value, `None` to remove the data, or a callable returning a replacement or `None`. Filtered parameter values must be excluded from cassette storage and from public cassette projections such as `cassette.requests[i].body`.

**Callbacks.** `before_record_request(request)` may mutate and return a request, or return `None` to skip recording that request. `before_record_response(response)` may mutate and return a response, or return `None` to skip recording the request/response pair.

**Compressed responses.** When `decode_compressed_response` is `True`, gzip and deflate response bodies must be decoded before recording and before response filters are applied. The decoded body must be stored as a string in the cassette. On replay from a cassette recorded with decoding, the `content-encoding` header must not be present in the replayed response.

**Ignoring hosts.** When `ignore_localhost` is `True`, requests to localhost-like hosts such as `localhost`, `127.0.0.1`, and `0.0.0.0` must not be recorded and must not be replayed. When `ignore_hosts=[...]` is set, requests to the specified hosts must not be recorded and must not be replayed. Both options may be combined. Ignored requests must proceed as normal network traffic as if VCR did not intercept them, and the cassette length must reflect only non-ignored interactions.

## Cassette Bookkeeping

The `Cassette` object maintains an ordered collection of recorded interactions and tracks playback state.

**Empty cassette.** A newly created `Cassette` must have zero length, an empty `requests` list, an empty `responses` list, a `play_count` of `0`, and `all_played` equal to `True`.

**Appending interactions.** `Cassette.append(request, response)` must add a request/response pair to the cassette. After appending, `len(cassette)` must reflect the new count, and `cassette.requests` must contain the appended request.

**Playback.** `Cassette.play_response(request)` must return the next matching recorded response for replay. After each replay, `play_count` must increment by one. `Cassette.responses_of(request)` must return all recorded responses matching the given request in their original appended order.

**Rewind.** `Cassette.rewind()` must reset playback state so that `play_count` returns to `0` and `all_played` returns to `False`, allowing all interactions to be replayed from the start.

**Playback repeats.** By default, each recorded response may be played only once per cassette use unless the cassette is rewound. When `allow_playback_repeats` is `True`, matching recorded responses may be replayed repeatedly, and `play_count` must increment on each replay.

**Drop unused.** When `drop_unused_requests` is `True`, saving a cassette must drop previously recorded interactions that were not used during the current cassette context.

## HTTP Interception

The implementation must intercept standard Python HTTP requests to enable the documented recording and replay workflows.

**Standard library support.** VCR must support the `urllib.request.urlopen` workflow, intercepting requests and returning responses that support reading the response body, status code, and headers.

**Requests library support.** When the `requests` dependency is installed, VCR must support `requests.get(...)`, `requests.post(...)`, and related method workflows, intercepting requests and returning `requests.Response`-compatible objects.

**Recording.** During recording, VCR must capture method, URL, headers, request body, response status, response headers, and response body. Redirect chains must record each individual request/response pair, and `cassette.requests` must reflect all recorded requests in order.

**Replay.** During replay, VCR must return a response object compatible enough with the calling client for the documented usage pattern, including reading the response body, status code, and headers. Multiple response header values must be preserved as lists. No real network request must be made for a matched interaction.

**Unpatching.** When a cassette context exits, HTTP patches must be restored so that subsequent requests outside the context are not intercepted by VCR. The `play_count` of an exited cassette must not change from subsequent requests made outside the context.

## State Model

The central shared state is a cassette: an ordered collection of recorded request/response interactions plus playback bookkeeping. Several public projections must agree with the cassette:

- the requests and responses visible on the `Cassette` object;
- matching decisions made from normalized `Request` objects;
- record-mode decisions about whether a new request can be recorded or must be rejected;
- serialized cassette files on disk;
- custom serializer, persister, matcher, filter, and patch configuration;
- context manager and decorator workflows.

## Error Semantics

Expose public errors for:

- unhandled requests that cannot be recorded or replayed under the current record mode;
- missing cassette data when a cassette is required;
- malformed cassette data;
- missing or malformed cassette data for custom persisters as documented.

Unhandled requests should raise a VCR-related exception. Custom persister loading should use the documented `CassetteNotFoundError` and `CassetteDecodeError`. Other invalid configuration should fail clearly without requiring a specific public exception hierarchy.

## Cross-View Invariants

These invariants define the implementation target:

1. The same normalized request fields must drive matching, cassette `requests`, filters, serializer output, and replay lookup.
2. Record mode decisions must agree with cassette existence, match results, playback state, and whether a request is saved.
3. Serializer and persister output must round-trip into an equivalent cassette that can replay the same interactions.
4. Filters and callbacks must affect both the saved cassette and the public `Cassette` projections.
5. Context managers and decorators must produce the same cassette lifecycle semantics.
6. Patches must be active only inside the cassette lifecycle and must be restored after success or failure.
7. Playback bookkeeping (`play_count`, `all_played`, repeats, rewind, drop-unused) must agree with actual replay behavior and saved cassette content.
8. VCR configuration defaults for `serializer`, `record_mode`, `match_on`, and `cassette_library_dir` must propagate to cassettes opened by that VCR instance, and per-cassette `use_cassette()` overrides must take precedence.
9. Record mode constants from `vcr.mode` must be interchangeable with their lowercase string equivalents wherever a record mode is accepted.

## Public Interface

### Import Surface

The project must be installable as a Python distribution that provides:

```python
import vcr
```

Top-level public objects:

```python
from vcr import VCR
from vcr import use_cassette
```

Documented public modules include:

```python
import vcr.config
import vcr.cassette
import vcr.matchers
import vcr.filters
import vcr.request
import vcr.serialize
import vcr.patch
import vcr.errors
import vcr.mode
import vcr.persisters.filesystem
```

The package must expose the public classes and functions implied by those documented modules. In particular, callers may import `Cassette` from `vcr.cassette`, `Request` from `vcr.request`, `serialize` and `deserialize` from `vcr.serialize`, `CannotOverwriteExistingCassetteException` from `vcr.errors`, and `FilesystemPersister`, `CassetteNotFoundError`, and `CassetteDecodeError` from `vcr.persisters.filesystem`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| VCR | class | Configured recorder with defaults for cassettes |
| use_cassette | function | Context manager and decorator for active cassettes |
| Cassette | class | In-memory cassette with requests, responses, and playback state |
| Cassette.load | classmethod | Load a cassette from a file path |
| Cassette.append | method | Add a request/response interaction to a cassette |
| Cassette.play_response | method | Return the next matching response for replay |
| Cassette.rewind | method | Reset playback state to replay from the start |
| Cassette.responses_of | method | Return all responses matching a given request |
| Request | class | Normalized outgoing HTTP request |
| CannotOverwriteExistingCassetteException | exception | Raised when record mode forbids a new request |
| CassetteNotFoundError | exception | Raised when a required cassette file is missing |
| CassetteDecodeError | exception | Raised when cassette data is malformed |
| FilesystemPersister | class | Default filesystem cassette persistence |
| serialize | function | Project cassette data into versioned interaction format |
| deserialize | function | Reconstruct requests and responses from interaction format |
| vcr.mode.ONCE | constant | Record mode: record once then replay only |
| vcr.mode.NONE | constant | Record mode: replay only and reject new requests |
| vcr.mode.NEW_EPISODES | constant | Record mode: replay existing and record new |
| vcr.mode.ALL | constant | Record mode: always record and never replay |
| VCR.register_matcher | method | Register a custom request matcher by name |
| VCR.register_serializer | method | Register a custom cassette serializer by name |
| VCR.register_persister | method | Register a custom cassette persister |
| VCR.ensure_suffix | method | Return a path transformer that enforces a cassette suffix |

### CLI Entry Points

VCR is a library-only package. It does not provide a console script, and `python -m vcr` is not a supported invocation. Applications use the documented Python imports and context-manager or decorator workflows.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility is determined through public imports, request normalization and matching, cassette state, record modes, serialization and persistence, filtering, patch lifecycle, and local HTTP record/replay workflows. Equivalent internal organization and semantically equivalent cassette formatting are acceptable.
