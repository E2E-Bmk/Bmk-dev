# Spec Test Map

Final S3_ORACLE_MERGE map for Track A public-API rewrites.

oracle_source: upstream_rewritten

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/rewritten_upstream_tests.py::test_new_creates_project_config_and_index | upstream | system_e2e | section Command Line | covered | Starter project creation and non-overwrite behavior from upstream new/CLI tests. |
| filter/rewritten_upstream_tests.py::test_new_preserves_existing_config_and_index | upstream | integration | section Command Line | covered | Starter project creation and non-overwrite behavior from upstream new/CLI tests. |
| filter/rewritten_upstream_tests.py::test_load_config_applies_keyword_overrides | upstream | integration | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_load_config_discovers_mkdocs_yml_before_yaml | upstream | integration | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_load_config_missing_default_file_raises_configuration_error | upstream | integration | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_unknown_config_key_is_warning_and_strict_aborts | upstream | atomic | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_yaml_env_tag_uses_environment_and_default | upstream | atomic | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_yaml_inherit_deep_merges_mappings_and_replaces_lists | upstream | integration | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_docs_dir_and_site_dir_may_not_contain_each_other | upstream | atomic | section Error Semantics | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_config_mapping_and_attribute_access_round_trip | upstream | atomic | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_config_options_validate_choice_list_and_optional | upstream | atomic | section Configuration Loading | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_file_directory_url_mapping | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_file_no_directory_url_mapping | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_file_generated_content_and_edit_uri | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_file_generated_requires_exactly_one_source | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_files_collection_replaces_filters_and_removes | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_copy_static_files_copies_included_non_markdown | upstream | integration | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_get_files_prefers_index_over_readme | upstream | integration | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_page_title_from_metadata_outranks_heading | upstream | atomic | section Pages, Metadata, Links, and Table of Contents | covered | Page, link, navigation, and cross-view behavior without private processors. |
| filter/rewritten_upstream_tests.py::test_page_title_from_heading_and_filename_fallback | upstream | atomic | section Pages, Metadata, Links, and Table of Contents | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_page_render_rewrites_internal_markdown_links | upstream | system_e2e | section Pages, Metadata, Links, and Table of Contents | covered | Page, link, navigation, and cross-view behavior without private processors. |
| filter/rewritten_upstream_tests.py::test_navigation_builds_sections_links_and_pages | upstream | system_e2e | section Navigation | covered | Page, link, navigation, and cross-view behavior without private processors. |
| filter/rewritten_upstream_tests.py::test_pages_omitted_from_explicit_nav_still_get_page_objects | upstream | system_e2e | section Cross-View Invariants | covered | Page, link, navigation, and cross-view behavior without private processors. |
| filter/rewritten_upstream_tests.py::test_theme_mapping_and_custom_dir_precedence | upstream | atomic | section Themes and Templates | covered | Theme/template public mapping and URL/script filter behavior. |
| filter/rewritten_upstream_tests.py::test_template_filters_normalize_urls_and_scripts | upstream | atomic | section Themes and Templates | covered | Theme/template public mapping and URL/script filter behavior. |
| filter/rewritten_upstream_tests.py::test_plugin_load_config_validates_schema | upstream | integration | section Plugins | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_plugin_collection_runs_events_in_priority_order | upstream | integration | section Plugins | covered | Public plugin configuration, collection, and event return semantics. |
| filter/rewritten_upstream_tests.py::test_plugin_event_returning_none_preserves_current_value | upstream | atomic | section Plugins | covered | Public plugin configuration, collection, and event return semantics. |
| filter/rewritten_upstream_tests.py::test_search_plugin_config_defaults_and_overrides | upstream | atomic | section Search | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_search_index_serializes_page_and_section_entries | upstream | system_e2e | section Search | covered | Page, link, navigation, and cross-view behavior without private processors. |
| filter/rewritten_upstream_tests.py::test_search_index_titles_mode_omits_section_entries | upstream | integration | section Search | covered | Search plugin/index public configuration and generated JSON behavior. |
| filter/rewritten_upstream_tests.py::test_url_helpers_preserve_external_urls_and_normalize_relative_paths | upstream | atomic | section Utilities | covered | Public utility behavior from upstream utility tests. |
| filter/rewritten_upstream_tests.py::test_file_and_path_utility_helpers | upstream | atomic | section Source Files and Generated Files | covered | Public File/Files mapping, generated content, discovery, and copy behavior. |
| filter/rewritten_upstream_tests.py::test_clean_directory_preserves_hidden_entries | upstream | atomic | section Utilities | covered | Public utility behavior from upstream utility tests. |
| filter/rewritten_upstream_tests.py::test_meta_parser_extracts_yaml_and_multimarkdown_metadata | upstream | atomic | section Utilities | covered | Configuration loading, validation, YAML, and option behavior from upstream config tests. |
| filter/rewritten_upstream_tests.py::test_count_handler_counts_records_by_level | upstream | atomic | section Utilities | covered | Public utility behavior from upstream utility tests. |
| filter/rewritten_upstream_tests.py::test_build_date_helpers_use_source_date_epoch | upstream | atomic | section Utilities | covered | Public utility behavior from upstream utility tests. |

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| filter/generated_tests.py::test_public_package_exposes_version_and_cli_group | generated | atomic | section Installable Surface + section Public API | covered | Public package exposes version and documented CLI command group. |
| filter/generated_tests.py::test_python_module_version_reports_installed_version | generated | system_e2e | section Installable Surface | covered | python -m mkdocs --version reports installed MkDocs version. |
| filter/generated_tests.py::test_load_config_rejects_missing_docs_dir | generated | atomic | section Exceptions and Error Semantics + section Error Semantics | covered | Config loader aborts on missing docs directory. |
| filter/generated_tests.py::test_project_config_defaults_include_site_and_theme | generated | integration | section Behavioral Sections + section Project Configuration Semantics | covered | Loaded project config applies documented site/theme/plugin defaults. |
| filter/generated_tests.py::test_build_api_writes_site_pages_and_search_assets | generated | system_e2e | section Build API | covered | Build API writes pages and search assets from public config. |
| filter/generated_tests.py::test_build_site_dir_override_keeps_config_and_output_consistent | generated | system_e2e | section Cross-View Invariants | covered | site_dir override matches config state and generated output location. |
| filter/generated_tests.py::test_strict_build_aborts_on_warning | generated | integration | section Error Semantics | covered | Strict build aborts when navigation warnings are emitted. |
| filter/generated_tests.py::test_plugin_lifecycle_events_run_during_build | generated | integration | section Plugins | covered | Plugin lifecycle hooks run during public build API. |
| filter/generated_tests.py::test_plugin_build_error_hook_observes_build_failure | generated | integration | section Exceptions and Error Semantics | covered | Plugin build_error hook observes public build failure. |
| filter/generated_tests.py::test_repo_url_and_site_url_shape_page_edit_links | generated | system_e2e | section Cross-View Invariants | covered | Repository and site URL settings are reflected in rendered output. |
| filter/generated_tests.py::test_custom_theme_directory_overrides_main_template | generated | integration | section Themes and Templates | covered | Custom theme directory overrides theme template output. |
| filter/generated_tests.py::test_validation_rejects_unknown_theme_name | generated | atomic | section Exceptions and Error Semantics | covered | Unknown theme name is reported as a handled configuration abort. |
| filter/generated_tests.py::test_full_new_then_build_workflow | generated | system_e2e | section Representative Workflow(s) | covered | End-to-end mkdocs new then build workflow creates a site. |

Total: 50 | kept (covered): 50 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 50
