# Stage 1 Candidate Notes: vcrpy-fullrepro-001

## Selection

Selected source repository: `repo-pool/kevin1024__vcrpy`

Task id: `vcrpy-fullrepro-001`

Snapshot:

- commit: `16b6c2651bddb9b62debc20f1f82a52c8a8ae5ba`
- source date: `2026-04-11 16:47:31 +0200`
- package: `vcr`
- non-test Python LOC: about 2,588 tracked nonblank/noncomment lines
- source modules: 29 tracked Python files under `vcr/`
- tests: about 292 pytest functions across unit and integration test files
- public docs: `README.rst`, `docs/usage.rst`, `docs/configuration.rst`, `docs/advanced.rst`, `docs/api.rst`

## Why This Candidate

VCR.py has a bounded but real multi-module product lifecycle:

- user code enters a `use_cassette()` context or decorator;
- outgoing HTTP requests are intercepted by library-specific patches/stubs;
- requests are normalized into `Request` objects;
- cassette state chooses record/replay behavior using record mode and matchers;
- responses are serialized/deserialized through registered serializers;
- cassette files are persisted and later reloaded;
- filters and custom matchers affect what is stored and what counts as the same request.

This creates cross-view invariants across config, patching, cassette memory state, request matching, serializers, persisters, and on-disk cassette content. A shallow implementation can pass individual helper tests while failing replay/record consistency.

## Public Source Boundary

Use public behavior from:

- `README.rst`
- `docs/usage.rst`
- `docs/configuration.rst`
- `docs/advanced.rst`
- `docs/api.rst`

`docs/api.rst` publicly documents:

- `vcr.config`
- `vcr.cassette`
- `vcr.matchers`
- `vcr.filters`
- `vcr.request`
- `vcr.serialize`
- `vcr.patch`

The top-level package behavior in README/usage also documents `vcr.use_cassette()` and `vcr.VCR`.

## Initial Risks

- The integration suite depends on optional packages such as `requests`, `urllib3`, `aiohttp`, `httpx`, `tornado`, `httplib2`, `pytest-httpbin`, `PyYAML`, and `wrapt`. The local scoring venv currently lacks these packages, so Stage 3 must either install a minimal dependency set or filter tests requiring unavailable ecosystems.
- Some integration tests may make local HTTP server requests or rely on pytest-httpbin fixtures. These are acceptable only if deterministic and local.
- Some tests may exercise library-specific stubs beyond the public docs. Stage 3 must map each retained test to public docs/API behavior.
- Avoid keeping tests whose module-level imports require optional dependencies not included in the allowed environment.

## Initial Filter Strategy

Prioritize:

- unit tests for `Cassette`, `Request`, record modes, matchers, filters, serializers, persisters, and VCR configuration;
- deterministic integration tests for `urllib.request`, `requests`, and local cassette read/write if dependencies can be installed;
- tests crossing at least two views: request object -> matcher -> cassette -> serializer/persister -> replay.

Filter or defer:

- tests for optional HTTP clients not installed in the benchmark environment;
- tests requiring live network access;
- tests whose only behavior is compatibility with undocumented internals;
- tests whose module-level imports force unavailable optional dependencies.

## Stage 1 Decision

Proceed to Stage 2.

The candidate is not as large as `sqlite-utils`, but it is more cohesive than a utility collection and has enough public lifecycle/state interaction to attempt a full-reproduction cleanroom task.
