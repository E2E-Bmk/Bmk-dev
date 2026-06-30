# vcrpy-fullrepro-001 Stage 3 Filter Map v5

Spec: ../spec/spec_v3.md
Collected input: collected_nodeids.txt (309 expanded nodeids; aiohttp collection error retained in collect_raw_current.txt and excluded as optional client surface).
Kept set: kept_nodeids.txt uses base nodeids so pytest expands parameterized tests and the scorer does not emit false not_collected rows.

## Reference Gate

- Final reference run: reference_score_filter_v5.json.
- Result: 38/38 passed; integration 16, system 22.
- Required local env for reproducibility: set REQUESTS_CA_BUNDLE to pytest_httpbin/certs/client.pem and clear proxy variables or set NO_PROXY=* for local httpbin traffic.

## v5 Corrections From Candidate Collection Audit

- Removed unit/test_filters.py entirely because module-level import requires uncontracted public function names such as `decode_response`; retained filter behavior is still covered through integration requests/cassette workflows.

## Keep Policy

Kept tests must be inferable from README/docs/api/usage/configuration/advanced plus public modules named in the spec, and their containing module must collect without requiring excluded private/legacy/optional surfaces. The filter excludes tests that depend on private underscore attributes, private connection stubs, proxy/wild/live-network fixtures, migration tooling, optional clients not promised by the spec, legacy parameters absent from spec, exact formatting, exact exception classes not contracted by spec, direct `Request.headers` public-property assertions, or module-level carriers that require those surfaces.

## Summary By Layer

- integration: 16 base nodeids
- system: 13 base nodeids

## Kept Nodeids

- `tests/integration/test_basic.py::test_basic_json_use` [system] - JSON serializer can record and replay a local HTTP interaction
- `tests/integration/test_basic.py::test_nonexistent_directory` [system] - use_cassette creates cassette paths and records local urllib traffic
- `tests/integration/test_basic.py::test_unpatch` [system] - HTTP patching is scoped to cassette lifecycle and cassette play_count remains consistent
- `tests/integration/test_config.py::test_default_set_cassette_library_dir` [integration] - cassette_library_dir resolves relative cassette names
- `tests/integration/test_config.py::test_dont_record_on_exception` [integration] - record_on_exception controls save behavior for context and decorator forms
- `tests/integration/test_config.py::test_override_match_on` [integration] - configured match_on controls replay matching
- `tests/integration/test_config.py::test_override_set_cassette_library_dir` [integration] - per-cassette overrides supersede VCR defaults
- `tests/integration/test_config.py::test_set_drop_unused_requests` [integration] - drop_unused_requests updates saved cassette interactions
- `tests/integration/test_ignore.py::test_ignore_httpbin` [integration] - ignore_hosts bypasses cassette recording/replay
- `tests/integration/test_ignore.py::test_ignore_localhost` [integration] - ignore_localhost bypasses cassette recording/replay
- `tests/integration/test_ignore.py::test_ignore_localhost_and_httpbin` [integration] - ignore rules compose
- `tests/integration/test_ignore.py::test_ignore_localhost_twice` [integration] - ignored requests remain normal across repeated cassette contexts
- `tests/integration/test_register_matcher.py::test_registered_false_matcher` [integration] - registered custom matcher can reject replay
- `tests/integration/test_register_matcher.py::test_registered_true_matcher` [integration] - registered custom matcher can enable replay
- `tests/integration/test_register_serializer.py::test_registered_serializer` [integration] - registered custom serializer is used for load/save lifecycle
- `tests/integration/test_request.py::test_recorded_request_uri_with_redirected_request` [integration] - recorded Request.uri reflects normalized redirected request sequence
- `tests/integration/test_request.py::test_records_multiple_header_values` [integration] - recorded response headers preserve multiple values for replay/storage
- `tests/integration/test_requests.py::test_body` [system] - requests client replay preserves response body
- `tests/integration/test_requests.py::test_cross_scheme` [system] - scheme participates in request identity across HTTP and HTTPS
- `tests/integration/test_requests.py::test_filter_post_params` [system] - post-data filtering affects recorded requests made by requests
- `tests/integration/test_requests.py::test_get_empty_content_type_json` [system] - body matcher handles empty JSON request bodies
- `tests/integration/test_requests.py::test_gzip__decode_compressed_response_false` [system] - requests compressed response replay works without forced decode
- `tests/integration/test_requests.py::test_gzip__decode_compressed_response_true` [system] - decode_compressed_response alters stored response and replay headers/body consistently
- `tests/integration/test_requests.py::test_headers` [system] - requests client replay preserves response headers
- `tests/integration/test_requests.py::test_post` [system] - requests POST record/replay preserves response content
- `tests/integration/test_requests.py::test_redirects` [system] - requests redirect workflow records and replays multiple interactions consistently
- `tests/integration/test_requests.py::test_status_code` [system] - requests client replay preserves status_code
- `tests/unit/test_unittest.py::test_vcr_kwargs_overridden` [integration] - VCRTestCase _get_vcr_kwargs customizes cassette defaults
- `tests/unit/test_unittest.py::test_vcr_kwargs_passed` [integration] - VCRTestCase passes explicit VCR kwargs through

## Major Dropped Surfaces

- aiohttp, httplib2, httpx, tornado, urllib3, boto3, proxy, wild/live-network tests: optional client or external service/proxy behavior outside spec scope.
- vcr.stubs / vcr.patch private connection internals and tests asserting `_path`, `_save`, `_match_on`, `_played_interactions`, `_new_interactions`: private implementation surface.
- migration/persist fixture compatibility tests and persister filesystem import-carrier rows: historical file format or undocumented module path beyond the behavioral spec.
- integration/test_filter.py and unit/test_filters.py rows: module-level imports require uncontracted helper symbols.
- unit/test_matchers.py, unit/test_request.py, unit/test_vcr.py rows: module-level imports/parametrization require unkept `HeadersDict`, `vcr.mode`, private stubs, or chunked/iterator body behavior.

## Dropped File Counts

- tests/integration/test_basic.py: 2 base nodeids dropped
- tests/integration/test_config.py: 2 base nodeids dropped
- tests/integration/test_disksaver.py: 2 base nodeids dropped
- tests/integration/test_filter.py: 11 base nodeids dropped
- tests/integration/test_matchers.py: 5 base nodeids dropped
- tests/integration/test_multiple.py: 1 base nodeids dropped
- tests/integration/test_proxy.py: 2 base nodeids dropped
- tests/integration/test_record_mode.py: 8 base nodeids dropped
- tests/integration/test_register_persister.py: 3 base nodeids dropped
- tests/integration/test_requests.py: 12 base nodeids dropped
- tests/integration/test_stubs.py: 4 base nodeids dropped
- tests/integration/test_urllib3.py: 11 base nodeids dropped
- tests/integration/test_wild.py: 6 base nodeids dropped
- tests/unit/test_cassettes.py: 32 base nodeids dropped
- tests/unit/test_errors.py: 1 base nodeids dropped
- tests/unit/test_filters.py: 24 base nodeids dropped
- tests/unit/test_json_serializer.py: 1 base nodeids dropped
- tests/unit/test_matchers.py: 12 base nodeids dropped
- tests/unit/test_migration.py: 3 base nodeids dropped
- tests/unit/test_persist.py: 2 base nodeids dropped
- tests/unit/test_request.py: 6 base nodeids dropped
- tests/unit/test_response.py: 4 base nodeids dropped
- tests/unit/test_serialize.py: 10 base nodeids dropped
- tests/unit/test_stubs.py: 4 base nodeids dropped
- tests/unit/test_unittest.py: 7 base nodeids dropped
- tests/unit/test_util.py: 2 base nodeids dropped
- tests/unit/test_vcr.py: 24 base nodeids dropped
- tests/unit/test_vcr_import.py: 1 base nodeids dropped
