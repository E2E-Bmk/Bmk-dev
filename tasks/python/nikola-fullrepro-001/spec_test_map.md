# nikola-fullrepro-001 Spec Test Map

oracle_version: 2026-07-18T15:05:00+08:00
filter/oracle_source: generated_only
track_a_summary: 537 upstream nodeids collected; upstream helpers and integration carriers require broad harness rewrite, and retaining the raw suite would exceed the Stage 1 expected_oracle_max=70. Track A was not used for final oracle; generated tests replace it with scoped public-behavior coverage.
track_b_summary: 84 generated tests; second generation pass targeted section coverage gaps in Installable Surface, Product State Model, Configuration/Metadata, Paths/Taxonomies, Plugin Contracts, Error Semantics, Cross-View Invariants, and Representative Workflows.
dummy_gate: real pytest invocation against /tmp/nikola-dummy; 0 passed, 48 failed, 36 errors.
reference_gate: 84 passed, 0 failed; pass_rate=1.0.
caveat: generated_only oracle requires Stage 5 spot-check gate.

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::test_package_version_is_public_string | generated | atomic | Installable Surface | covered | Targeted Track B installable/public entry-point behavior observed from reference. |
| oracle/test_atomic.py::test_debug_flags_are_booleans | generated | atomic | Installable Surface | covered | Targeted Track B installable/public entry-point behavior observed from reference. |
| oracle/test_atomic.py::test_slugify_ascii_words | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_slugify_polish_diacritics | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_slugify_removes_unsafe_punctuation | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_unslugify_simple_slug | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_unslugify_multiple_words | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_encodelink_escapes_spaces | generated | atomic | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_atomic.py::test_encodelink_escapes_unicode | generated | atomic | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_atomic.py::test_encodelink_preserves_existing_percent_encoding | generated | atomic | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_atomic.py::test_translation_candidate_adds_language_before_extension | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_translation_candidate_removes_language_for_default | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_translation_candidate_extension_language_pattern | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_translation_candidate_extension_language_default | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_translation_candidate_preserves_directory_and_compound_extension | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_true_word | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_yes_word | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_one_string | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_false_word | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_no_word | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_accepts_zero_string | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_uses_blank_value_for_missing_key | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_bool_from_meta_uses_fallback_for_unknown_text | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_write_metadata_nikola_format_contains_declared_fields | generated | atomic | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_create_redirect_writes_redirect_document | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_load_data_reads_json_mapping | generated | atomic | Public API | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_apply_shortcodes_replaces_single_shortcode | generated | atomic | Shortcodes And Filters | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_apply_shortcodes_passes_body_to_shortcode | generated | atomic | Shortcodes And Filters | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_extract_shortcodes_replaces_shortcode_with_token | generated | atomic | Shortcodes And Filters | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_unknown_shortcode_with_exceptions_returns_empty_output | generated | atomic | Shortcodes And Filters | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_init_creates_project_configuration | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_init_creates_content_directories | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_new_post_creates_slugged_post_source | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_new_post_source_contains_title_metadata | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_new_post_source_contains_slug_metadata | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_new_post_source_contains_tags_metadata | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_atomic.py::test_new_page_creates_page_source | generated | atomic | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_output_directory | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_site_index | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_post_output_page | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_page_output | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_archive_output | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_category_index | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_category_pages_for_post_tags | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_rss_feed | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_build_creates_sitemap | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_generated_post_page_contains_post_title | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_generated_index_links_to_post | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_generated_rss_mentions_post | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_generated_sitemap_mentions_post_url | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_check_command_accepts_generated_site | generated | system_e2e | Compilation, Rendering, And Generated Files | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_version_command_is_configuration_free | generated | integration | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_help_command_is_configuration_free | generated | integration | Project Initialization And CLI Commands | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_unknown_command_returns_failure | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_build_without_configuration_returns_failure | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_surface_top_level_nikola_constructs_configured_site | generated | integration | Installable Surface | covered | Targeted Track B installable/public entry-point behavior observed from reference. |
| oracle/test_atomic.py::test_surface_console_version_entry_runs_without_conf | generated | atomic | Installable Surface | covered | Targeted Track B installable/public entry-point behavior observed from reference. |
| oracle/test_atomic.py::test_surface_public_utils_module_is_importable_and_operational | generated | atomic | Installable Surface | covered | Targeted Track B installable/public entry-point behavior observed from reference. |
| oracle/test_integration.py::test_state_model_has_config_content_and_generated_projections | generated | system_e2e | Product State Model | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_state_model_source_title_is_visible_in_generated_projection | generated | system_e2e | Product State Model | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_state_model_tag_metadata_is_visible_in_taxonomy_projection | generated | system_e2e | Product State Model | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_configuration_file_declares_post_and_page_patterns | generated | system_e2e | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_post_source_contains_required_metadata_fields | generated | system_e2e | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_page_source_contains_page_metadata | generated | system_e2e | Configuration, Content, And Metadata | covered | Generated Track B public-behavior test; expected value observed from reference. |
| oracle/test_integration.py::test_registered_path_handler_returns_configured_path | generated | integration | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_integration.py::test_registered_path_handler_link_path_has_leading_slash | generated | integration | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_integration.py::test_relative_link_between_pretty_url_pages | generated | integration | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_integration.py::test_taxonomy_outputs_match_post_tags | generated | system_e2e | Paths, Links, And Taxonomies | covered | Targeted Track B path/link/taxonomy behavior observed from reference public API or generated files. |
| oracle/test_integration.py::test_command_plugin_receives_active_site | generated | integration | Plugin And Task Contracts | covered | Targeted Track B plugin contract test using public plugin category behavior observed from reference. |
| oracle/test_integration.py::test_task_and_compiler_plugins_receive_same_site_object | generated | integration | Plugin And Task Contracts | covered | Targeted Track B plugin contract test using public plugin category behavior observed from reference. |
| oracle/test_integration.py::test_shortcode_plugin_registers_handler_on_site | generated | integration | Plugin And Task Contracts | covered | Targeted Track B plugin contract test using public plugin category behavior observed from reference. |
| oracle/test_integration.py::test_invalid_config_file_returns_nonzero | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_missing_config_file_returns_nonzero | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_invalid_command_option_returns_nonzero | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_duplicate_new_post_returns_nonzero | generated | integration | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_atomic.py::test_malformed_shortcode_raises_parsing_error | generated | atomic | Error Semantics | covered | Targeted Track B error-path test; asserts exception type or non-success status, not message text. |
| oracle/test_integration.py::test_cross_view_post_source_generates_matching_output_path | generated | system_e2e | Cross-View Invariants | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_cross_view_index_feed_and_sitemap_reference_post | generated | system_e2e | Cross-View Invariants | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_cross_view_tag_metadata_matches_category_outputs | generated | system_e2e | Cross-View Invariants | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_cross_view_page_source_generates_page_output | generated | system_e2e | Cross-View Invariants | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_cross_view_check_accepts_same_generated_projection | generated | system_e2e | Cross-View Invariants | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_workflow_init_new_post_build_check_created_site | generated | system_e2e | Representative Workflows | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_workflow_register_and_apply_site_shortcode | generated | integration | Representative Workflows | covered | Targeted Track B test binding config/content/generated projections observed from reference. |
| oracle/test_integration.py::test_workflow_register_path_handler_and_resolve_link | generated | integration | Representative Workflows | covered | Targeted Track B test binding config/content/generated projections observed from reference. |

Total: 84 | kept (covered): 84 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 84
Layer counts: atomic=40 | integration=17 | system_e2e=27 | integration+system_e2e=44

Section counts:
- Compilation, Rendering, And Generated Files: 14
- Configuration, Content, And Metadata: 9
- Cross-View Invariants: 5
- Error Semantics: 7
- Installable Surface: 5
- Paths, Links, And Taxonomies: 7
- Plugin And Task Contracts: 3
- Product State Model: 3
- Project Initialization And CLI Commands: 9
- Public API: 15
- Representative Workflows: 3
- Shortcodes And Filters: 4
