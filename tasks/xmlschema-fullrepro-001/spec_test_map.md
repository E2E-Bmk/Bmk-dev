# Specification To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_schema_constructs_from_local_xsd` | atomic | Scope | covered |
| 2 | `oracle/test_atomic.py::test_schema_constructs_from_text_with_base_url` | atomic | Scope | covered |
| 3 | `oracle/test_atomic.py::test_build_switch_controls_public_built_state` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_schema_namespaces_expose_include_and_import_targets` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_schema_maps_expose_root_element_and_named_types` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_schema_component_lookup_returns_public_element` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_schema_get_schema_resolves_loaded_namespace` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_package_is_valid_accepts_valid_fixture` | atomic | Validation And Error Reporting | covered |
| 9 | `oracle/test_atomic.py::test_package_is_valid_rejects_invalid_fixture` | atomic | Validation And Error Reporting | covered |
| 10 | `oracle/test_atomic.py::test_package_validate_accepts_valid_fixture` | atomic | Validation And Error Reporting | covered |
| 11 | `oracle/test_atomic.py::test_package_iter_errors_returns_structured_errors` | atomic | Validation And Error Reporting | covered |
| 12 | `oracle/test_atomic.py::test_schema_validate_and_is_valid_share_result` | atomic | Validation And Error Reporting | covered |
| 13 | `oracle/test_atomic.py::test_schema_iter_errors_is_empty_for_valid_fixture` | atomic | Validation And Error Reporting | covered |
| 14 | `oracle/test_atomic.py::test_to_dict_returns_decoded_mapping` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_to_json_returns_json_text` | atomic | Scope | covered |
| 16 | `oracle/test_atomic.py::test_to_json_writes_to_text_stream` | atomic | Scope | covered |
| 17 | `oracle/test_atomic.py::test_to_etree_encodes_public_mapping` | atomic | Scope | covered |
| 18 | `oracle/test_atomic.py::test_package_to_etree_encodes_using_schema` | atomic | Scope | covered |
| 19 | `oracle/test_atomic.py::test_from_json_encodes_json_text` | atomic | Scope | covered |
| 20 | `oracle/test_atomic.py::test_default_converter_has_public_converter_contract` | atomic | Scope | covered |
| 21 | `oracle/test_atomic.py::test_parker_converter_changes_root_projection` | atomic | Scope | covered |
| 22 | `oracle/test_atomic.py::test_badgerfish_converter_projects_attributes` | atomic | Scope | covered |
| 23 | `oracle/test_atomic.py::test_jsonml_converter_projects_tagged_sequence` | atomic | Scope | covered |
| 24 | `oracle/test_atomic.py::test_columnar_converter_projects_named_columns` | atomic | Scope | covered |
| 25 | `oracle/test_atomic.py::test_xml_resource_reports_local_url` | atomic | Scope | covered |
| 26 | `oracle/test_atomic.py::test_xml_resource_none_policy_blocks_local_file` | atomic | Error Semantics | covered |
| 27 | `oracle/test_atomic.py::test_fetch_resource_normalizes_local_path` | atomic | Scope | covered |
| 28 | `oracle/test_atomic.py::test_fetch_schema_returns_local_schema_url` | atomic | Scope | covered |
| 29 | `oracle/test_atomic.py::test_fetch_namespaces_reads_local_xml` | atomic | Scope | covered |
| 30 | `oracle/test_atomic.py::test_etree_element_is_accepted_as_document_source` | atomic | Scope | covered |
| 31 | `oracle/test_atomic.py::test_schema_export_returns_location_mapping` | atomic | Scope | covered |
| 32 | `oracle/test_atomic.py::test_schema_component_iteration_exposes_public_components` | atomic | Product State Model | covered |
| 33 | `oracle/test_integration.py::test_decode_and_json_projections_agree_on_business_fields` | integration | Cross-View Invariants | covered |
| 34 | `oracle/test_integration.py::test_stream_json_and_json_encoding_round_trip` | integration | Representative Workflows | covered |
| 35 | `oracle/test_integration.py::test_invalid_document_reports_false_and_nonempty_error_projection` | integration | Error Semantics | covered |
| 36 | `oracle/test_integration.py::test_text_schema_base_url_resolves_both_local_dependencies` | integration | Representative Workflows | covered |
| 37 | `oracle/test_integration.py::test_deferred_build_then_component_iteration_produces_same_root` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_exported_schema_bundle_reloads_and_validates` | integration | Representative Workflows | covered |
| 39 | `oracle/test_integration.py::test_add_schema_extends_existing_component_map` | integration | Product State Model | covered |
| 40 | `oracle/test_integration.py::test_import_and_include_state_is_visible_after_build` | integration | Product State Model | covered |
| 41 | `oracle/test_integration.py::test_parker_decode_then_encode_preserves_validity` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_badgerfish_decode_then_encode_preserves_attribute` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_jsonml_decode_then_encode_preserves_root_name` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_columnar_decode_then_encode_preserves_root_name` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_package_etree_projection_can_be_validated_again` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_json_file_projection_encodes_and_validates` | integration | Representative Workflows | covered |
| 47 | `oracle/test_integration.py::test_element_tree_source_decodes_same_customer` | integration | Scope | covered |
| 48 | `oracle/test_integration.py::test_local_resource_can_be_validated_and_decoded` | integration | Scope | covered |
| 49 | `oracle/test_integration.py::test_resource_policy_allows_local_but_rejects_none` | integration | Error Semantics | covered |
| 50 | `oracle/test_integration.py::test_export_location_map_points_to_local_xsd_files` | integration | Representative Workflows | covered |
| 51 | `oracle/test_integration.py::test_namespace_projection_matches_schema_validation` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_maps_and_root_elements_agree_on_global_order` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_component_iteration_contains_imported_public_element` | integration | Product State Model | covered |
| 54 | `oracle/test_integration.py::test_json_options_make_pretty_output_without_changing_data` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_lax_decode_returns_data_and_error_tuple_for_invalid_input` | integration | Error Semantics | covered |
| 56 | `oracle/test_integration.py::test_error_projection_preserves_path_or_reason_without_message_matching` | integration | Error Semantics | covered |
| 57 | `oracle/test_integration.py::test_converter_instance_and_converter_class_have_same_default_fields` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_cli_validate_command_reports_success` | integration | Representative Workflows | covered |
| 59 | `oracle/test_integration.py::test_cli_validate_command_reports_failure` | integration | Error Semantics | covered |
| 60 | `oracle/test_integration.py::test_cli_xml2json_writes_deterministic_local_output` | integration | Representative Workflows | covered |
| 61 | `oracle/test_integration.py::test_cli_json2xml_rehydrates_output_and_validates` | integration | Representative Workflows | covered |
| 62 | `oracle/test_integration.py::test_cli_xml2json_skips_existing_output_without_force` | integration | Representative Workflows | covered |
| 63 | `oracle/test_integration.py::test_cli_converter_option_changes_json_shape` | integration | Representative Workflows | covered |
| 64 | `oracle/test_integration.py::test_schema_and_package_validation_accept_same_element` | integration | Cross-View Invariants | covered |

final_scoreable: 64
