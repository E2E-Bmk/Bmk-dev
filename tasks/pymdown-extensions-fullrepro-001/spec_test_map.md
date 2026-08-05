# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_slugify_lower_percent_encoding_callback` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_slugify_case_modes_are_documented` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_legacy_slug_helpers_match_documented_modes` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_blocks_validator_rejects_invalid_html_identifier` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_emoji_indexes_return_documented_structure` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_emoji_default_generators_honor_options_and_alt_text` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_emoji_non_strict_unknown_shortname_remains_literal` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_superfences_public_div_formatter_escapes_source` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_superfences_public_code_formatter_escapes_source_and_attrs` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_superfences_highlight_validator_separates_options_and_attrs` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_arithmatex_inline_formatter_generic_output` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_arithmatex_fenced_formatter_generic_output` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_arithmatex_legacy_mathjax_formatter_remains_callable` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_snippets_missing_file_raises_when_check_paths_enabled` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_superfences_exception_from_formatter_propagates` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_inlinehilite_exception_from_formatter_propagates` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_emoji_strict_unknown_shortname_raises_runtime_error` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_striphtml_removes_on_attributes_and_comments` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_highlight_non_pygments_javascript_shape` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_arithmatex_generic_normalizes_dollar_math` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_arithmatex_smart_dollar_avoids_currency_false_positive` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_tasklist_custom_clickable_checkbox_shape` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_blocks_invalid_option_leaves_source_literal` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_legacy_details_open_marker_renders_details_open` | atomic | Product State Model | covered |
| 25 | `oracle/test_atomic.py::test_caret_and_tilde_disabled_features_remain_literal` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_generated_html_does_not_include_external_css_for_tasklist` | atomic | Product State Model | covered |
| 27 | `oracle/test_atomic.py::test_striphtml_does_not_sanitize_tag_names_or_text_content` | atomic | Product State Model | covered |
| 28 | `oracle/test_atomic.py::test_magiclink_does_not_verify_remote_repository_existence` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_smartsymbols_disabled_family_remains_literal` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_progressbar_level_class_uses_configured_increment` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_keys_custom_separator_and_class` | atomic | Product State Model | covered |
| 32 | `oracle/test_atomic.py::test_quotes_callout_uses_blockquote_public_syntax` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_slugify_strips_html_and_uses_custom_separator` | atomic | Product State Model | covered |
| 34 | `oracle/test_atomic.py::test_blocks_validators_accept_precise_public_types` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_blocks_validator_combinators_convert_or_reject_values` | atomic | Product State Model | covered |
| 36 | `oracle/test_atomic.py::test_smartsymbols_replaces_arrows_and_ordinals` | atomic | Product State Model | covered |
| 37 | `oracle/test_atomic.py::test_critic_accept_and_reject_modes_select_different_text` | atomic | Product State Model | covered |
| 38 | `oracle/test_atomic.py::test_installable_extension_modules_expose_make_extension` | atomic | Product State Model | covered |
| 39 | `oracle/test_atomic.py::test_installable_extension_strings_load_independently` | atomic | Product State Model | covered |
| 40 | `oracle/test_atomic.py::test_b64_rewrites_allowed_local_png` | atomic | Product State Model | covered |
| 41 | `oracle/test_atomic.py::test_b64_leaves_disallowed_parent_path_unchanged` | atomic | Product State Model | covered |
| 42 | `oracle/test_atomic.py::test_pathconverter_preserves_fragment_while_rewriting_path` | atomic | Product State Model | covered |
| 43 | `oracle/test_atomic.py::test_snippets_inserted_markdown_is_rendered` | atomic | Product State Model | covered |
| 44 | `oracle/test_atomic.py::test_magiclink_shorthand_uses_configured_repo_context` | atomic | Product State Model | covered |
| 45 | `oracle/test_atomic.py::test_blocks_attrs_visible_on_outer_element` | atomic | Product State Model | covered |
| 46 | `oracle/test_atomic.py::test_blocks_admonition_renders_title_and_markdown_content` | atomic | Product State Model | covered |
| 47 | `oracle/test_atomic.py::test_blocks_details_open_option_controls_outer_element` | atomic | Product State Model | covered |
| 48 | `oracle/test_atomic.py::test_legacy_tabbed_groups_consecutive_tabs` | atomic | Product State Model | covered |
| 49 | `oracle/test_integration.py::test_extra_bundle_enables_tables_and_footnotes` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_extra_routes_subextension_configuration` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_markdown_instance_reset_clears_tab_group_counter` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_markdown_instance_reset_clears_caption_numbering` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_markdown_instance_reset_preserves_extension_configuration` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_emoji_generator_receives_alias_information` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_superfences_custom_fence_receives_options_and_attrs` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_inlinehilite_custom_inline_receives_language_and_class` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_registration_replacement_with_superfences_and_fenced_code_is_single_output` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_legacy_tabbed_and_blocks_tab_share_output_classes` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_saneheaders_preserves_issue_like_line_for_magiclink` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_representative_documentation_workflow_combines_public_projections` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_representative_documentation_workflow_missing_snippet_raises` | integration | Cross-View Invariants | covered |
| 62 | `oracle/test_integration.py::test_representative_math_workflow_combines_inlinehilite_and_superfences` | integration | Cross-View Invariants | covered |
| 63 | `oracle/test_integration.py::test_highlight_configuration_shared_with_superfences_non_pygments` | integration | Cross-View Invariants | covered |
| 64 | `oracle/test_integration.py::test_inline_plain_text_default_language_uses_highlight_class` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_snippets_line_selection_flows_into_markdown_rendering` | integration | Cross-View Invariants | covered |
| 66 | `oracle/test_integration.py::test_superfences_uses_highlight_code_attr_on_pre_configuration` | integration | Cross-View Invariants | covered |
| 67 | `oracle/test_integration.py::test_superfences_nested_blockquote_preserves_quote_and_code_views` | integration | Cross-View Invariants | covered |
| 68 | `oracle/test_integration.py::test_tasklist_and_smartsymbols_transform_same_list_item` | integration | Cross-View Invariants | covered |
| 69 | `oracle/test_integration.py::test_keys_and_quotes_extensions_preserve_inline_keyboard_content_in_callout` | integration | Cross-View Invariants | covered |
| 70 | `oracle/test_integration.py::test_critic_and_smartsymbols_compose_without_losing_inline_replacements` | integration | Cross-View Invariants | covered |
| 71 | `oracle/test_integration.py::test_local_asset_rewriters_preserve_semantic_links_and_embed_allowed_images` | integration | Cross-View Invariants | covered |
| 72 | `oracle/test_integration.py::test_blocks_attribute_and_admonition_extensions_share_nested_markdown_state` | integration | Cross-View Invariants | covered |
| 73 | `oracle/test_integration.py::test_progressbar_and_tasklist_extensions_keep_distinct_block_projections` | integration | Cross-View Invariants | covered |

final_scoreable: 73
