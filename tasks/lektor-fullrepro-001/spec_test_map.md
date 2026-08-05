# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_project_from_file_reads_name_tree_and_themes` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_project_from_path_finds_the_only_project_file` | atomic | Scope | covered |
| 3 | `oracle/test_atomic.py::test_project_discover_walks_up_from_a_nested_content_directory` | atomic | Representative Workflows | covered |
| 4 | `oracle/test_atomic.py::test_project_content_path_from_filename_maps_content_records` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_project_output_path_uses_the_configured_relative_directory` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_environment_config_exposes_project_url_and_alternatives` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_metaformat_tokenize_reads_scalar_and_multiline_fields` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_metaformat_serialize_round_trips_multiline_values` | atomic | Cross-View Invariants | covered |
| 9 | `oracle/test_atomic.py::test_pad_root_loads_system_fields_and_typed_values` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_pad_get_normalizes_equivalent_record_paths` | atomic | Scope | covered |
| 11 | `oracle/test_atomic.py::test_pad_get_returns_none_for_a_missing_record` | atomic | Error Semantics | covered |
| 12 | `oracle/test_atomic.py::test_record_mapping_access_exposes_field_values` | atomic | Installable Surface | covered |
| 13 | `oracle/test_atomic.py::test_record_url_path_uses_alternative_prefixes` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_record_parent_and_child_relationships` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_record_visibility_flags_reflect_explicit_system_fields` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_pad_resolve_url_path_skips_invisible_records_by_default` | atomic | Error Semantics | covered |
| 17 | `oracle/test_atomic.py::test_pad_resolve_url_path_can_include_hidden_records` | atomic | Error Semantics | covered |
| 18 | `oracle/test_atomic.py::test_query_visibility_options_are_independent` | atomic | Scope | covered |
| 19 | `oracle/test_atomic.py::test_query_filter_uses_public_record_expression_proxy` | atomic | Installable Surface | covered |
| 20 | `oracle/test_atomic.py::test_query_order_limit_offset_and_count_are_composable` | atomic | Installable Surface | covered |
| 21 | `oracle/test_atomic.py::test_query_get_and_first_find_records_by_local_id` | atomic | Installable Surface | covered |
| 22 | `oracle/test_atomic.py::test_query_distinct_collects_scalar_values_and_multiline_tags` | atomic | Installable Surface | covered |
| 23 | `oracle/test_atomic.py::test_alternative_fallback_preserves_requested_language` | atomic | Cross-View Invariants | covered |
| 24 | `oracle/test_atomic.py::test_get_alts_reports_existing_translations_and_fallbacks` | atomic | Product State Model | covered |
| 25 | `oracle/test_atomic.py::test_record_url_to_builds_a_relative_child_link` | atomic | Installable Surface | covered |
| 26 | `oracle/test_atomic.py::test_pad_make_url_uses_the_configured_base_url` | atomic | Installable Surface | covered |
| 27 | `oracle/test_atomic.py::test_datamodel_exposes_custom_fields_and_child_policy` | atomic | Product State Model | covered |
| 28 | `oracle/test_atomic.py::test_string_field_trims_whitespace_and_uses_the_first_line` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_integer_and_boolean_fields_convert_raw_values` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_date_and_datetime_fields_convert_raw_values` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_markdown_field_renders_as_markup_for_a_record` | atomic | Cross-View Invariants | covered |
| 32 | `oracle/test_atomic.py::test_datamodel_to_json_describes_field_types_and_names` | atomic | Cross-View Invariants | covered |
| 33 | `oracle/test_atomic.py::test_asset_root_exposes_static_files_and_artifact_paths` | atomic | Product State Model | covered |
| 34 | `oracle/test_atomic.py::test_attachment_record_exposes_type_url_and_source_file` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_environment_selects_html_autoescape_by_filename` | atomic | Installable Surface | covered |
| 36 | `oracle/test_atomic.py::test_environment_render_template_exposes_this_and_site` | atomic | Cross-View Invariants | covered |
| 37 | `oracle/test_atomic.py::test_builder_declares_a_page_artifact` | atomic | Installable Surface | covered |
| 38 | `oracle/test_atomic.py::test_builder_marks_a_built_artifact_current` | atomic | Cross-View Invariants | covered |
| 39 | `oracle/test_atomic.py::test_build_program_primary_artifact_is_the_built_page` | atomic | Installable Surface | covered |
| 40 | `oracle/test_atomic.py::test_cli_project_info_json_matches_project_projection` | atomic | Representative Workflows | covered |
| 41 | `oracle/test_atomic.py::test_cli_content_file_info_json_maps_a_record_path` | atomic | Representative Workflows | covered |
| 42 | `oracle/test_integration.py::test_query_and_template_render_share_the_same_record_values` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_alternative_record_and_template_use_the_requested_language` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_filtered_and_ordered_query_drives_a_stable_result_projection` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_visibility_options_and_url_resolution_agree_for_hidden_content` | integration | Error Semantics | covered |
| 46 | `oracle/test_integration.py::test_pagination_records_expose_page_numbers_and_sliced_items` | integration | Product State Model | covered |
| 47 | `oracle/test_integration.py::test_attachment_query_and_attachment_record_share_tree_metadata` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_model_fields_reach_records_and_model_json_together` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_markdown_field_and_page_template_produce_html` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_environment_rendering_and_record_url_to_use_one_pad_context` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_builder_builds_root_template_into_index_artifact` | integration | Representative Workflows | covered |
| 52 | `oracle/test_integration.py::test_builder_builds_child_pages_and_attachments_to_expected_artifacts` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_builder_build_all_produces_pages_attachments_and_assets` | integration | Representative Workflows | covered |
| 54 | `oracle/test_integration.py::test_builder_reuses_a_current_artifact_on_the_second_build` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_builder_rebuilds_an_artifact_when_its_template_changes` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_builder_rebuilds_an_artifact_when_a_record_changes` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_builder_prune_removes_an_artifact_after_a_page_becomes_hidden` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_cli_build_matches_the_direct_builder_render` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_cli_build_reuses_output_without_an_existing_files_prompt` | integration | Representative Workflows | covered |
| 60 | `oracle/test_integration.py::test_cli_project_info_text_and_json_agree` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_cli_content_file_info_text_and_json_agree` | integration | Cross-View Invariants | covered |
| 62 | `oracle/test_integration.py::test_cli_project_info_short_alias_resolves_to_the_same_command` | integration | Representative Workflows | covered |
| 63 | `oracle/test_integration.py::test_query_distinct_values_and_template_tags_share_the_same_source_data` | integration | Cross-View Invariants | covered |
| 64 | `oracle/test_integration.py::test_nested_record_urls_resolve_back_to_the_same_records` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_alternative_build_produces_a_language_prefixed_artifact` | integration | Cross-View Invariants | covered |
| 66 | `oracle/test_integration.py::test_cli_source_info_only_indexes_without_rendering` | integration | Representative Workflows | covered |
| 67 | `oracle/test_integration.py::test_cli_relative_output_path_is_resolved_from_the_working_directory` | integration | Representative Workflows | covered |
| 68 | `oracle/test_integration.py::test_asset_inclusion_and_exclusion_rules_reach_the_asset_build_queue` | integration | Cross-View Invariants | covered |
| 69 | `oracle/test_integration.py::test_model_child_order_reaches_pagination_and_template_output` | integration | Cross-View Invariants | covered |
| 70 | `oracle/test_integration.py::test_sibling_navigation_uses_the_parent_model_order` | integration | Product State Model | covered |
| 71 | `oracle/test_integration.py::test_model_file_dependency_rebuilds_a_page_artifact` | integration | Cross-View Invariants | covered |
| 72 | `oracle/test_integration.py::test_query_transformations_leave_the_original_query_unchanged` | integration | Cross-View Invariants | covered |
| 73 | `oracle/test_integration.py::test_build_output_preserves_autoescaped_markup_and_markdown_markup` | integration | Cross-View Invariants | covered |
| 74 | `oracle/test_integration.py::test_direct_environment_and_cli_project_use_the_same_project_tree` | integration | Cross-View Invariants | covered |
| 75 | `oracle/test_integration.py::test_build_state_records_template_and_model_dependencies` | integration | Cross-View Invariants | covered |
| 76 | `oracle/test_integration.py::test_cli_content_file_info_rejects_a_file_outside_the_project` | integration | Error Semantics | covered |
| 77 | `oracle/test_integration.py::test_pad_url_modes_are_shared_by_record_url_to_and_explicit_modes` | integration | Cross-View Invariants | covered |
| 78 | `oracle/test_integration.py::test_build_all_and_source_database_preserve_content_paths` | integration | Cross-View Invariants | covered |
| 79 | `oracle/test_integration.py::test_environment_template_globals_can_query_the_same_pad` | integration | Cross-View Invariants | covered |

final_scoreable: 79
