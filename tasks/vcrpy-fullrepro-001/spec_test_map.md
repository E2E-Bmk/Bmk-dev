# vcrpy-fullrepro-001 Stage 3 Filter Map v6

Spec: spec_v3.md
oracle_source: upstream_filtered
oracle_version: filter_v6_error_semantics_20260703
repair_note: Adds four upstream public Error Semantics tests after Stage 5 Gate D found zero Error Semantics coverage.
reference_gate: previous filter_v5 reference 38/38 plus v6 Error Semantics supplement 4/4

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| tests/integration/test_basic.py::test_basic_json_use | upstream | system_e2e | Serializers | covered | JSON serializer can record and replay a local HTTP interaction |
| tests/integration/test_basic.py::test_nonexistent_directory | upstream | system_e2e | Core Workflow | covered | use_cassette creates cassette paths and records local urllib traffic |
| tests/integration/test_basic.py::test_unpatch | upstream | system_e2e | HTTP Interception | covered | HTTP patching is scoped to cassette lifecycle and cassette play_count remains consistent |
| tests/integration/test_config.py::test_default_set_cassette_library_dir | upstream | integration | VCR Configuration | covered | cassette_library_dir resolves relative cassette names |
| tests/integration/test_config.py::test_dont_record_on_exception | upstream | integration | Exception Handling And Saving | covered | record_on_exception controls save behavior for context and decorator forms |
| tests/integration/test_config.py::test_override_match_on | upstream | integration | Request Matching | covered | configured match_on controls replay matching |
| tests/integration/test_config.py::test_override_set_cassette_library_dir | upstream | integration | VCR Configuration | covered | per-cassette overrides supersede VCR defaults |
| tests/integration/test_config.py::test_set_drop_unused_requests | upstream | integration | Playback Repeats And Drop Unused | covered | drop_unused_requests updates saved cassette interactions |
| tests/integration/test_ignore.py::test_ignore_httpbin | upstream | integration | Ignoring Requests | covered | ignore_hosts bypasses cassette recording/replay |
| tests/integration/test_ignore.py::test_ignore_localhost | upstream | integration | Ignoring Requests | covered | ignore_localhost bypasses cassette recording/replay |
| tests/integration/test_ignore.py::test_ignore_localhost_and_httpbin | upstream | integration | Ignoring Requests | covered | ignore rules compose |
| tests/integration/test_ignore.py::test_ignore_localhost_twice | upstream | integration | Ignoring Requests | covered | ignored requests remain normal across repeated cassette contexts |
| tests/integration/test_register_matcher.py::test_registered_false_matcher | upstream | integration | Request Matching | covered | registered custom matcher can reject replay |
| tests/integration/test_register_matcher.py::test_registered_true_matcher | upstream | integration | Request Matching | covered | registered custom matcher can enable replay |
| tests/integration/test_register_serializer.py::test_registered_serializer | upstream | integration | Serializers | covered | registered custom serializer is used for load/save lifecycle |
| tests/integration/test_request.py::test_recorded_request_uri_with_redirected_request | upstream | integration | Request Public API | covered | recorded Request.uri reflects normalized redirected request sequence |
| tests/integration/test_request.py::test_records_multiple_header_values | upstream | integration | HTTP Interception | covered | recorded response headers preserve multiple values for replay/storage |
| tests/integration/test_requests.py::test_body | upstream | system_e2e | HTTP Interception | covered | requests client replay preserves response body |
| tests/integration/test_requests.py::test_cross_scheme | upstream | system_e2e | Cross-View Invariants | covered | scheme participates in request identity across HTTP and HTTPS |
| tests/integration/test_requests.py::test_filter_post_params | upstream | system_e2e | Filters And Callbacks | covered | post-data filtering affects recorded requests made by requests |
| tests/integration/test_requests.py::test_get_empty_content_type_json | upstream | system_e2e | Request Matching | covered | body matcher handles empty JSON request bodies |
| tests/integration/test_requests.py::test_gzip__decode_compressed_response_false | upstream | system_e2e | Filters And Callbacks | covered | requests compressed response replay works without forced decode |
| tests/integration/test_requests.py::test_gzip__decode_compressed_response_true | upstream | system_e2e | Filters And Callbacks | covered | decode_compressed_response alters stored response and replay headers/body consistently |
| tests/integration/test_requests.py::test_headers | upstream | system_e2e | HTTP Interception | covered | requests client replay preserves response headers |
| tests/integration/test_requests.py::test_post | upstream | system_e2e | HTTP Interception | covered | requests POST record/replay preserves response content |
| tests/integration/test_requests.py::test_redirects | upstream | system_e2e | Cross-View Invariants | covered | requests redirect workflow records and replays multiple interactions consistently |
| tests/integration/test_requests.py::test_status_code | upstream | system_e2e | HTTP Interception | covered | requests client replay preserves status_code |
| tests/unit/test_unittest.py::test_vcr_kwargs_overridden | upstream | integration | Unittest Integration | covered | VCRTestCase _get_vcr_kwargs customizes cassette defaults |
| tests/unit/test_unittest.py::test_vcr_kwargs_passed | upstream | integration | Unittest Integration | covered | VCRTestCase passes explicit VCR kwargs through |
| tests/integration/test_record_mode.py::test_once_record_mode | upstream | integration | Error Semantics | covered | record mode once rejects unmatched requests when an existing cassette cannot record new traffic |
| tests/integration/test_record_mode.py::test_none_record_mode | upstream | integration | Error Semantics | covered | record mode none rejects new requests when no cassette data is available |
| tests/integration/test_record_mode.py::test_none_record_mode_with_existing_cassette | upstream | integration | Error Semantics | covered | record mode none replays existing matches but rejects new unmatched requests |
| tests/integration/test_register_persister.py::test_load_cassette_persister_exception_handling | upstream | integration | Error Semantics | covered | custom persister not-found/decode errors are treated as empty cassettes while unexpected errors propagate |
| filter/generated_tests.py::test_request_exposes_normalized_uri_components_and_aliases | generated | atomic | Request Public API | covered | Request exposes normalized URI components and backwards-compatible aliases |
| filter/generated_tests.py::test_request_applies_default_http_and_https_ports | generated | atomic | Request Public API | covered | Request applies default ports for HTTP and HTTPS |
| filter/generated_tests.py::test_request_query_preserves_repeated_values_in_sorted_order | generated | atomic | Request Public API | covered | Request query parsing preserves repeated values in deterministic order |
| filter/generated_tests.py::test_uri_matcher_accepts_equal_uri_and_rejects_different_uri | generated | atomic | Request Matching | covered | URI matcher compares only the complete request URI |
| filter/generated_tests.py::test_headers_matcher_is_case_insensitive_and_detects_value_changes | generated | atomic | Request Matching | covered | Header matcher treats names case-insensitively and values exactly |
| filter/generated_tests.py::test_body_matcher_compares_json_semantically | generated | atomic | Request Matching | covered | JSON body matcher ignores object key ordering while detecting value changes |
| filter/generated_tests.py::test_serialize_projects_ordered_request_response_interactions | generated | atomic | Serializers | covered | Serialization preserves request-response pairing and interaction order |
| filter/generated_tests.py::test_deserialize_reconstructs_request_and_response_from_interaction | generated | atomic | Serializers | covered | Deserialization reconstructs public Request and response projections |

Total: 41 | kept (covered): 41 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 41
