# VCR.py Reconstruction Spec v3

## Product Overview

Build an installable Python package named `vcr`. VCR.py records HTTP interactions made by user code into cassette files and replays them on later runs. The package lets tests become deterministic by intercepting outgoing HTTP requests, matching them to recorded requests, and returning the previously recorded responses instead of performing network traffic.

## Product State Model

The central shared state is a cassette: an ordered collection of recorded request/response interactions plus playback bookkeeping. Several public projections must agree with the cassette:

- the requests and responses visible on the `Cassette` object;
- matching decisions made from normalized `Request` objects;
- record-mode decisions about whether a new request can be recorded or must be rejected;
- serialized cassette files on disk;
- custom serializer, persister, matcher, filter, and patch configuration;
- context manager, decorator, and unittest workflows.

## Scope

Implement the public behavior needed for practical VCR.py usage:

- `import vcr`;
- `vcr.VCR` configuration objects;
- module-level `vcr.use_cassette()`;
- `Cassette` objects returned from cassette contexts;
- normalized `Request` objects;
- record and replay behavior for Python HTTP requests in deterministic local tests;
- request matchers and custom matcher registration;
- request/response filtering before recording;
- serializers and custom serializer registration;
- persisters and custom persister registration;
- automatic cassette naming for decorators;
- cassette rewinding, playback-repeat control, exception-save control, and drop-unused behavior;
- unittest helper classes.

No live internet access is required. Local HTTP servers used by callers should be enough to exercise record and replay behavior.

## Non-Goals

- No requirement to support every third-party HTTP client ecosystem unless its behavior is shown in the public package docs and the dependency is installed.
- No requirement to reproduce private implementation modules or private helper functions.
- No requirement to provide pytest plugins; the docs point to separate packages for pytest integration.
- No requirement to maintain byte-for-byte formatting of cassette files beyond semantically equivalent serialization.
- No requirement to make live external HTTP calls during replay.

## Installable Surface

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
import vcr.persisters.filesystem
import vcr.unittest
```

The package should also expose the public classes and functions implied by those documented modules, including configuration, cassette, request, matcher, filter, serializer, patch, persistence, and unittest APIs. In particular, callers may import `Cassette`, `Request`, `CannotOverwriteExistingCassetteException`, `FilesystemPersister`, `CassetteNotFoundError`, `CassetteDecodeError`, `VCRMixin`, and `VCRTestCase` from their documented modules.

## Core Workflow

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

Callers can create a configured recorder:

```python
my_vcr = vcr.VCR(
    serializer="json",
    cassette_library_dir="fixtures/cassettes",
    record_mode="once",
    match_on=["uri", "method"],
)
```

Required behavior:

- Configuration options on a `VCR` object provide defaults for cassettes created by that object.
- Keyword arguments passed to `use_cassette()` override the corresponding `VCR` defaults for that cassette.
- A module-level `vcr.use_cassette()` behaves like using a default `VCR` instance.
- `cassette_library_dir`, when set, is used to resolve relative cassette paths and automatic cassette names.
- `serializer`, `record_mode`, `match_on`, filters, callbacks, patch settings, and cassette behavior flags must affect the cassette opened by `use_cassette()`.
- The default serializer writes YAML cassette files when PyYAML is available.
- The default record mode is `once`.

## Record Modes

Support these record modes:

- `once`: replay recorded interactions; if no cassette file exists, record new interactions; if a cassette file exists, reject new unmatched requests.
- `new_episodes`: replay recorded interactions and record new unmatched interactions.
- `none`: replay recorded interactions and reject every new unmatched request.
- `all`: record new interactions and do not replay existing interactions.

Record-mode decisions must be based on whether the current request matches an unused or repeat-allowed recorded interaction in the active cassette.

When a new request is rejected, raise a public VCR error that lets callers distinguish an unhandled HTTP request from normal transport failures.

## Cassette Public API

The `Cassette` object exposed by a context manager is part of the public API.

Required public properties and behavior:

- `requests`: ordered list of recorded `Request` objects.
- `responses`: ordered list of recorded response dictionaries/objects corresponding to requests.
- `play_count`: number of response playbacks performed by this cassette instance.
- `all_played`: true when all recorded responses have been played at least once, considering repeat and rewind behavior.
- `responses_of(request)`: return responses matching a given `Request`.
- `allow_playback_repeats`: controls whether the same recorded response can be replayed more than once without rewinding.
- `len(cassette)` should reflect the number of recorded interactions.
- `rewind()` resets playback bookkeeping so recorded interactions can be played again.

The cassette must keep request order stable. Recording, replaying, rewinding, and saving must update the public cassette projections consistently.

## Request Public API

The `Request` object represents a normalized outgoing HTTP request.

Required properties:

- `uri`: full request URI.
- `scheme`: request scheme such as `http` or `https`.
- `host`: target host.
- `port`: target port, including default-port handling sufficient for matching.
- `path`: request path.
- `query`: parsed and sorted query parameters as name/value pairs.
- `method`: HTTP method.
- `body`: request body, usually empty for GET.
Backwards-compatible aliases:

- `url` aliases `uri`.
- `protocol` aliases `scheme`.

Requests must be serializable into cassette files and reconstructable when a cassette is loaded. Header information must be available to the extent needed for documented header matching, filtering, recording, and replay, without requiring `headers` to be a public `Request` property.

## Request Matching

Default matching uses:

```python
["method", "scheme", "host", "port", "path", "query"]
```

Built-in matcher names:

- `method`
- `uri`
- `scheme`
- `host`
- `port`
- `path`
- `query`
- `raw_body`
- `body`
- `headers`

Required behavior:

- A request matches a recorded request only if all configured matchers agree.
- `body` matching compares the request body after unmarshalling by content type for XML-RPC, JSON, and form-urlencoded bodies, falling back to `raw_body` when unmarshalling does not apply.
- A matcher may report mismatch by returning false or by raising `AssertionError`.
- Custom matchers can be registered with `VCR.register_matcher(name, callable)`.
- After registration, callers may use the matcher name in `match_on`.
- Matcher failures should produce useful mismatch information where practical.

## Serializers

VCR supports cassette serialization and deserialization.

Required behavior:

- Built-in YAML serialization should be available when PyYAML is installed.
- Built-in JSON serialization should be available.
- A serializer object/module can be registered with `VCR.register_serializer(name, serializer)`.
- A serializer must provide `serialize(cassette_dict)` and `deserialize(cassette_string)`.
- After registration, callers may use the serializer by setting `serializer=name` on a VCR object or cassette.
- Serialized cassette data must preserve enough request, response, and playback-relevant information to replay interactions later.

## Persisters

VCR supports custom cassette persistence.

Required behavior:

- The default filesystem persister loads and saves cassette files.
- `VCR.register_persister(persister)` registers a custom persister.
- A persister must provide `load_cassette` and `save_cassette` methods with the documented load/save behavior.
- Loading a missing cassette should raise `CassetteNotFoundError`.
- Loading malformed cassette data should raise `CassetteDecodeError`.

## Filters And Callbacks

VCR can remove or replace sensitive information before recording.

Configuration options:

- `filter_headers`
- `filter_query_parameters`
- `filter_post_data_parameters`
- `before_record_request`
- `before_record_response`
- `decode_compressed_response`

Required behavior:

- Header, query, and post-data filters accept simple key names or `(key, replacement)` pairs.
- A replacement may be a static value, `None` to remove the data, or a callable returning a replacement or `None`.
- `before_record_request(request)` may mutate and return a request, or return `None` to skip recording that request.
- `before_record_response(response)` may mutate and return a response, or return `None` to skip recording the request/response pair.
- If `decode_compressed_response` is enabled, gzip/deflate response bodies are decoded before recording and before response filters are applied.
- Filtering affects cassette storage and later public cassette projections.

## Ignoring Requests

Required behavior:

- `ignore_localhost=True` ignores requests to localhost-like hosts such as `localhost`, `127.0.0.1`, and `0.0.0.0`.
- `ignore_hosts=[...]` ignores requests to configured hosts.
- Requests ignored by VCR are not saved in the cassette and are not replayed from it.
- Ignored requests should proceed as normal network traffic as if VCR did not notice them.

## Custom Patches

VCR supports `custom_patches`, where each patch identifies a target object/module, an attribute name, and a replacement object.

Required behavior:

- Custom patches are applied when a cassette context is entered.
- Custom patches are restored when the cassette context exits.
- Custom patches compose with the normal cassette lifecycle.

## Automatic Cassette Naming

When `use_cassette` is used as a decorator without an explicit path:

- Both `@my_vcr.use_cassette` and `@my_vcr.use_cassette()` are valid decorator forms.
- The cassette path is generated from the decorated function name.
- If no `cassette_library_dir` is configured, the cassette is placed next to the file containing the decorated function when that location is discoverable.
- If `cassette_library_dir` is configured, the generated cassette is placed in that directory.
- `path_transformer` and `func_path_generator` can customize generated paths.
- `VCR.ensure_suffix(".yaml")` returns a transformer that ensures generated cassette paths use the requested suffix.

## Exception Handling And Saving

Required behavior:

- By default, VCR saves cassette data when leaving a context even if the enclosed code raises an exception.
- If `record_on_exception=False`, VCR does not save newly recorded cassette data when the enclosed code raises an exception.
- Patches must still be restored when exceptions occur.

## Playback Repeats And Drop Unused

Required behavior:

- By default, each recorded response can be played only once per cassette use unless the cassette is rewound.
- If `allow_playback_repeats=True`, matching recorded responses may be replayed repeatedly.
- If `drop_unused_requests=True`, saving a cassette drops previously recorded interactions that were not used during the current cassette context.

## Unittest Integration

Provide `vcr.unittest.VCRTestCase` and `vcr.unittest.VCRMixin`.

Required behavior:

- `VCRTestCase` automatically wraps each test method in a cassette.
- The active cassette is available as `self.cassette`.
- Default cassette names use the test class and method name and are stored under a `cassettes` directory next to the test.
- Subclasses can customize `_get_vcr_kwargs`, `_get_cassette_library_dir`, `_get_cassette_name`, and `_get_vcr`.
- `VCRMixin` provides the same cassette behavior for use with other unittest class hierarchies.

## HTTP Interception

The implementation must intercept standard Python HTTP requests well enough for public VCR.py workflows.

Required behavior:

- Support the documented standard-library `urllib.request` workflow.
- Support the documented `requests.get(...)` workflow when the `requests` dependency is installed.
- During recording, capture method, URL, headers, request body, response status, response headers, and response body.
- During replay, return a response object compatible enough with the calling client for the documented usage pattern, especially reading the response body.
- During replay, no real network request should be made for a matched interaction.

## Cross-View Invariants

These invariants define the implementation target:

- The same normalized request fields must drive matching, cassette `requests`, filters, serializer output, and replay lookup.
- Record mode decisions must agree with cassette existence, match results, playback state, and whether a request is saved.
- Serializer and persister output must round-trip into an equivalent cassette that can replay the same interactions.
- Filters and callbacks must affect both the saved cassette and the public `Cassette` projections.
- Context managers, decorators, and unittest integration must produce the same cassette lifecycle semantics.
- Patches must be active only inside the cassette lifecycle and must be restored after success or failure.
- Playback bookkeeping (`play_count`, `all_played`, repeats, rewind, drop-unused) must agree with actual replay behavior and saved cassette content.

## Error Semantics

Expose public errors for:

- unhandled requests that cannot be recorded or replayed under the current record mode;
- missing cassette data when a cassette is required;
- malformed cassette data;
- missing or malformed cassette data for custom persisters as documented.

Unhandled requests should raise a VCR-related exception. Custom persister loading should use the documented `CassetteNotFoundError` and `CassetteDecodeError`. Other invalid configuration should fail clearly without requiring a specific public exception hierarchy.

## Implementation Freedom

Any internal architecture is acceptable if the public behavior above holds. You may use Python standard-library HTTP facilities and common installed dependencies implied by the docs. Do not require live internet access for tests that replay recorded local interactions.

## Invocation Protocol

VCR.py is a library-only package. It does not provide a console script, and `python -m vcr` is not a supported invocation. Applications and test suites use the documented Python imports and context-manager, decorator, or unittest workflows.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Validation exercises public imports, request normalization and matching, cassette state, record modes, serialization and persistence, filtering, patch lifecycle, unittest integration, and local HTTP record/replay workflows. Equivalent internal organization and semantically equivalent cassette formatting are acceptable.
