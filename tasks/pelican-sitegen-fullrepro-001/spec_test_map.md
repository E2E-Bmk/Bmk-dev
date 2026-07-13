# Spec Test Map

oracle_version: 20260704-public-carrier-v1
oracle_source: generated_public_carrier
spec: spec/spec_v3.md
carrier: filter/public_carrier
reference_score: filter/reference_score.json
candidate_score: candidate-runs/codex-pelican-specv3-20260701-001/score_result_public_carrier_wsl_20260704.json (Linux/WSL, 40 passed / 16 failed / 0 collection_error)
merge_note: Replaces the retired upstream test-package oracle with public-carrier tests using documented CLI/API/file-output behavior. The carrier imports only documented public Pelican modules and no private underscore helpers.

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| tests/test_public_pelican_behavior.py::test_01_default_settings_include_default_language | generated | atomic | section Installable Surface | covered | default language is part of public defaults |
| tests/test_public_pelican_behavior.py::test_02_pelican_package_exposes_version_string | generated | atomic | section Installable Surface | covered | package exposes public version metadata |
| tests/test_public_pelican_behavior.py::test_03_pelican_package_exports_main_classes | generated | atomic | section Installable Surface | covered | package exports main public class |
| tests/test_public_pelican_behavior.py::test_04_read_settings_applies_explicit_override | generated | atomic | section Settings | covered | explicit overrides win in read_settings |
| tests/test_public_pelican_behavior.py::test_05_read_settings_keeps_unspecified_defaults | generated | atomic | section Settings | covered | default values remain when unspecified |
| tests/test_public_pelican_behavior.py::test_06_read_settings_normalizes_output_path_override | generated | atomic | section Settings | covered | path-like override is accepted |
| tests/test_public_pelican_behavior.py::test_07_parse_arguments_decodes_json_extra_settings | generated | atomic | section Command-Line Workflows | covered | CLI extra settings parse JSON values |
| tests/test_public_pelican_behavior.py::test_08_parse_arguments_accepts_multiple_extra_settings | generated | atomic | section Command-Line Workflows | covered | multiple CLI extra settings combine |
| tests/test_public_pelican_behavior.py::test_09_parse_arguments_rejects_missing_equals | generated | atomic | section Error Semantics | covered | invalid extra-setting syntax raises ValueError |
| tests/test_public_pelican_behavior.py::test_10_parse_arguments_rejects_non_json_value | generated | atomic | section Error Semantics | covered | non-JSON CLI values raise ValueError |
| tests/test_public_pelican_behavior.py::test_11_get_config_turns_cli_overrides_into_settings | generated | atomic | section Settings | covered | get_config returns settings derived from parsed CLI |
| tests/test_public_pelican_behavior.py::test_12_get_config_respects_relative_urls_flag | generated | atomic | section Command-Line Workflows | covered | relative URL flag becomes effective setting |
| tests/test_public_pelican_behavior.py::test_13_slugify_uses_regex_substitutions_for_url_parts | generated | atomic | section URL, Output, and Feed Rules | covered | slugify applies public substitution rules |
| tests/test_public_pelican_behavior.py::test_14_slugify_can_preserve_case | generated | atomic | section URL, Output, and Feed Rules | covered | slugify preserve_case is observable |
| tests/test_public_pelican_behavior.py::test_15_posixize_path_uses_forward_slashes | generated | atomic | section URL, Output, and Feed Rules | covered | paths normalize to forward slashes |
| tests/test_public_pelican_behavior.py::test_16_path_to_url_keeps_forward_slash_urls | generated | atomic | section URL, Output, and Feed Rules | covered | URL path helper preserves URL separators |
| tests/test_public_pelican_behavior.py::test_17_get_date_parses_pelican_datetime_metadata | generated | atomic | section Content and Metadata Behavior | covered | date metadata parses to datetime |
| tests/test_public_pelican_behavior.py::test_18_author_slug_url_and_save_path_agree | generated | atomic | section Content Objects | covered | author wrapper slug/url/save_as agree |
| tests/test_public_pelican_behavior.py::test_19_category_slug_url_and_save_path_agree | generated | atomic | section Content Objects | covered | category wrapper slug/url/save_as agree |
| tests/test_public_pelican_behavior.py::test_20_tag_slug_url_and_save_path_agree | generated | atomic | section Content Objects | covered | tag wrapper slug/url/save_as agree |
| tests/test_public_pelican_behavior.py::test_21_urlwrapper_as_dict_exposes_name_and_slug | generated | atomic | section Content Objects | covered | wrapper dictionary exposes public name/slug |
| tests/test_public_pelican_behavior.py::test_22_readers_read_markdown_content_and_metadata | generated | atomic | section Readers | covered | Markdown reader returns content object and metadata |
| tests/test_public_pelican_behavior.py::test_23_reader_reports_unknown_extension_as_unsupported | generated | atomic | section Error Semantics | covered | unsupported reader extension raises TypeError |
| tests/test_public_pelican_behavior.py::test_24_public_signal_namespaces_share_generation_signal | generated | atomic | section Plugins and Signals | covered | package and plugin signal namespaces agree |
| tests/test_public_pelican_behavior.py::test_25_plugin_signal_namespace_exposes_content_object_signal | generated | atomic | section Plugins and Signals | covered | plugin signal namespace exposes public signal |
| tests/test_public_pelican_behavior.py::test_26_paginator_reports_count_and_page_range | generated | atomic | section Writers and Pagination | covered | paginator exposes count/page range |
| tests/test_public_pelican_behavior.py::test_27_paginator_first_page_has_next_only | generated | atomic | section Writers and Pagination | covered | first page has next/no previous |
| tests/test_public_pelican_behavior.py::test_28_paginator_middle_page_has_neighbors | generated | atomic | section Writers and Pagination | covered | middle page has next and previous |
| tests/test_public_pelican_behavior.py::test_29_pagination_rule_is_public_three_field_tuple | generated | atomic | section Writers and Pagination | covered | PaginationRule exposes three public fields |
| tests/test_public_pelican_behavior.py::test_30_generated_article_uses_configured_save_path | generated | integration | section Site Generation | covered | Pelican writes configured article output path |
| tests/test_public_pelican_behavior.py::test_31_article_template_receives_title_metadata | generated | integration | section Content and Metadata Behavior | covered | template receives article title metadata |
| tests/test_public_pelican_behavior.py::test_32_article_template_receives_url_metadata | generated | integration | section Cross-View Invariants | covered | template URL agrees with configured article URL |
| tests/test_public_pelican_behavior.py::test_33_article_template_receives_save_as_metadata | generated | integration | section Cross-View Invariants | covered | template save_as agrees with configured output file |
| tests/test_public_pelican_behavior.py::test_34_article_template_receives_category_metadata | generated | integration | section Content and Metadata Behavior | covered | template receives category metadata |
| tests/test_public_pelican_behavior.py::test_35_article_template_receives_author_metadata | generated | integration | section Content and Metadata Behavior | covered | template receives author metadata |
| tests/test_public_pelican_behavior.py::test_36_article_template_receives_tag_metadata | generated | integration | section Content and Metadata Behavior | covered | template receives tag metadata |
| tests/test_public_pelican_behavior.py::test_37_article_template_receives_summary_metadata | generated | integration | section Content and Metadata Behavior | covered | template receives summary metadata |
| tests/test_public_pelican_behavior.py::test_38_static_link_renders_to_site_url | generated | integration | section Cross-View Invariants | covered | rendered static link agrees with SITEURL and static path |
| tests/test_public_pelican_behavior.py::test_39_static_file_is_copied_to_output | generated | integration | section Cross-View Invariants | covered | static link corresponds to copied output file |
| tests/test_public_pelican_behavior.py::test_40_index_contains_published_article | generated | integration | section Content and Metadata Behavior | covered | index lists published article |
| tests/test_public_pelican_behavior.py::test_41_hidden_article_has_output_file | generated | integration | section Content and Metadata Behavior | covered | hidden article still writes output file |
| tests/test_public_pelican_behavior.py::test_42_hidden_article_is_not_listed_on_index | generated | integration | section Cross-View Invariants | covered | hidden output is excluded from index view |
| tests/test_public_pelican_behavior.py::test_43_draft_article_uses_draft_output_location | generated | integration | section Content and Metadata Behavior | covered | draft uses draft output path |
| tests/test_public_pelican_behavior.py::test_44_draft_article_is_not_listed_on_index | generated | integration | section Cross-View Invariants | covered | draft output is excluded from index view |
| tests/test_public_pelican_behavior.py::test_45_page_uses_page_url_and_save_path | generated | integration | section Cross-View Invariants | covered | page template URL matches page setting |
| tests/test_public_pelican_behavior.py::test_46_page_template_receives_page_body | generated | integration | section Themes and Templates | covered | template override receives page body |
| tests/test_public_pelican_behavior.py::test_47_category_page_is_generated_for_article_category | generated | integration | section URL, Output, and Feed Rules | covered | category page generated from article metadata |
| tests/test_public_pelican_behavior.py::test_48_tag_pages_are_generated_for_each_tag | generated | integration | section URL, Output, and Feed Rules | covered | tag pages generated from article metadata |
| tests/test_public_pelican_behavior.py::test_49_author_pages_are_generated_for_each_author | generated | integration | section URL, Output, and Feed Rules | covered | author pages generated from author metadata |
| tests/test_public_pelican_behavior.py::test_50_all_articles_feed_is_generated | generated | integration | section URL, Output, and Feed Rules | covered | Atom feed file generated |
| tests/test_public_pelican_behavior.py::test_51_feed_entry_uses_same_article_title_as_page | generated | system_e2e | section Cross-View Invariants | covered | feed title matches generated article page |
| tests/test_public_pelican_behavior.py::test_52_feed_entry_uses_same_article_url_as_page | generated | system_e2e | section Cross-View Invariants | covered | feed link matches generated article URL |
| tests/test_public_pelican_behavior.py::test_53_feed_excludes_hidden_and_draft_articles | generated | system_e2e | section Cross-View Invariants | covered | feed excludes hidden and draft views |
| tests/test_public_pelican_behavior.py::test_54_category_feed_uses_category_slug | generated | system_e2e | section URL, Output, and Feed Rules | covered | category feed uses category slug |
| tests/test_public_pelican_behavior.py::test_55_generated_output_contains_no_source_markdown_files | generated | system_e2e | section Site Generation | covered | generated output omits source markdown |
| tests/test_public_pelican_behavior.py::test_56_cli_and_programmatic_settings_describe_same_site_name | generated | system_e2e | section Cross-View Invariants | covered | CLI and programmatic settings agree for same site name |

Total: 56 | kept (covered): 56 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 56
