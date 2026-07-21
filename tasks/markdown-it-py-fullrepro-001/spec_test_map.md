# Spec-Test Map

oracle_version: 2026-07-20-native-v1
spec_version: v1
filter/oracle_source: upstream_rewritten
scorer_isolation: task-local native tests with the selected package first on PYTHONPATH

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::test_get_rules | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_get_rules |
| oracle/test_atomic.py::test_load_presets | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_load_presets |
| oracle/test_atomic.py::test_override_options | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_override_options |
| oracle/test_atomic.py::test_enable | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_enable |
| oracle/test_atomic.py::test_disable | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_disable |
| oracle/test_atomic.py::test_reset | upstream_rewritten | atomic | Parser Configuration And Rule Control | covered | source: tests/test_api/test_main.py::test_reset |
| oracle/test_atomic.py::test_parseInline | upstream_rewritten | integration | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_parseInline |
| oracle/test_atomic.py::test_renderInline | upstream_rewritten | integration | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_renderInline |
| oracle/test_atomic.py::test_emptyStr | upstream_rewritten | atomic | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_emptyStr |
| oracle/test_atomic.py::test_empty_env | upstream_rewritten | atomic | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_empty_env |
| oracle/test_atomic.py::test_fragments_join_merges_adjacent_text_tokens | upstream_rewritten | integration | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_fragments_join_merges_adjacent_text_tokens |
| oracle/test_atomic.py::test_text_join_merges_adjacent_text_special_tokens | upstream_rewritten | integration | Inline Parsing And Token Joining | covered | source: tests/test_api/test_main.py::test_text_join_merges_adjacent_text_special_tokens |
| oracle/test_integration.py::TestColonFenceMarker::test_basic | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_basic |
| oracle/test_integration.py::TestColonFenceMarker::test_with_info | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_with_info |
| oracle/test_integration.py::TestColonFenceMarker::test_colon_in_info_allowed | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_colon_in_info_allowed |
| oracle/test_integration.py::TestColonFenceMarker::test_longer_closing | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_longer_closing |
| oracle/test_integration.py::TestColonFenceMarker::test_shorter_closing_no_match | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_shorter_closing_no_match |
| oracle/test_integration.py::TestColonFenceMarker::test_does_not_interfere_with_backtick | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_does_not_interfere_with_backtick |
| oracle/test_integration.py::TestColonFenceMarker::test_unclosed_block | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestColonFenceMarker::test_unclosed_block |
| oracle/test_integration.py::TestExactMatch::test_exact_match_same_length | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestExactMatch::test_exact_match_same_length |
| oracle/test_integration.py::TestExactMatch::test_exact_match_longer_no_close | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestExactMatch::test_exact_match_longer_no_close |
| oracle/test_integration.py::TestExactMatch::test_exact_match_shorter_no_close | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestExactMatch::test_exact_match_shorter_no_close |
| oracle/test_integration.py::TestExactMatch::test_nesting_pattern | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestExactMatch::test_nesting_pattern |
| oracle/test_integration.py::TestExactMatch::test_unclosed_exact_match | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestExactMatch::test_unclosed_exact_match |
| oracle/test_integration.py::TestOverrideStandardFence::test_override_with_exact_match | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestOverrideStandardFence::test_override_with_exact_match |
| oracle/test_integration.py::TestOverrideStandardFence::test_override_add_colon_marker | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestOverrideStandardFence::test_override_add_colon_marker |
| oracle/test_integration.py::TestOverrideStandardFence::test_override_preserves_backtick_info_restriction | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestOverrideStandardFence::test_override_preserves_backtick_info_restriction |
| oracle/test_integration.py::TestMinMarkers::test_min_markers_default | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestMinMarkers::test_min_markers_default |
| oracle/test_integration.py::TestMinMarkers::test_min_markers_custom | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestMinMarkers::test_min_markers_custom |
| oracle/test_integration.py::TestDisallowMarkerInInfo::test_default_backtick_disallowed | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestDisallowMarkerInInfo::test_default_backtick_disallowed |
| oracle/test_integration.py::TestDisallowMarkerInInfo::test_tilde_in_tilde_info_allowed | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestDisallowMarkerInInfo::test_tilde_in_tilde_info_allowed |
| oracle/test_integration.py::TestDisallowMarkerInInfo::test_disallow_all | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestDisallowMarkerInInfo::test_disallow_all |
| oracle/test_integration.py::TestDisallowMarkerInInfo::test_disallow_none | upstream_rewritten | integration | Fence Rule Factory | covered | source: tests/test_api/test_make_fence_rule.py::TestDisallowMarkerInInfo::test_disallow_none |
| oracle/test_plugin.py::test_inline_after | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_inline_after |
| oracle/test_plugin.py::test_inline_before | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_inline_before |
| oracle/test_plugin.py::test_inline_at | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_inline_at |
| oracle/test_plugin.py::test_block_after | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_block_after |
| oracle/test_plugin.py::test_block_before | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_block_before |
| oracle/test_plugin.py::test_block_at | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_block_at |
| oracle/test_plugin.py::test_core_after | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_core_after |
| oracle/test_plugin.py::test_core_before | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_core_before |
| oracle/test_plugin.py::test_core_at | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_core_at |
| oracle/test_plugin.py::test_add_terminator_char | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_add_terminator_char |
| oracle/test_plugin.py::test_add_terminator_char_idempotent | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_add_terminator_char_idempotent |
| oracle/test_plugin.py::test_add_terminator_char_rebuilds | upstream_rewritten | integration | Plugin Rule Registration | covered | source: tests/test_api/test_plugin_creation.py::test_add_terminator_char_rebuilds |
| oracle/test_token.py::test_token | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_api/test_token.py::test_token |
| oracle/test_token.py::test_serialization | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_api/test_token.py::test_serialization |
| oracle/test_cli.py::test_parse | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_parse |
| oracle/test_cli.py::test_parse_fail | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_parse_fail |
| oracle/test_cli.py::test_non_utf8 | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_non_utf8 |
| oracle/test_cli.py::test_print_heading | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_print_heading |
| oracle/test_cli.py::test_interactive | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_interactive |
| oracle/test_cli.py::test_main_no_args_is_interactive | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_main_no_args_is_interactive |
| oracle/test_cli.py::test_parse_output | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_parse_output |
| oracle/test_cli.py::test_stdin | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_stdin |
| oracle/test_cli.py::test_multiple_files | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_multiple_files |
| oracle/test_cli.py::test_interactive_render | upstream_rewritten | system_e2e | Command-Line Workflows | covered | source: tests/test_cli.py::test_interactive_render |
| oracle/test_tree.py::test_tree_to_tokens_conversion | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_tree.py::test_tree_to_tokens_conversion |
| oracle/test_tree.py::test_property_passthrough | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_tree.py::test_property_passthrough |
| oracle/test_tree.py::test_type | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_tree.py::test_type |
| oracle/test_tree.py::test_sibling_traverse | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_tree.py::test_sibling_traverse |
| oracle/test_tree.py::test_walk | upstream_rewritten | integration | Token And Syntax Tree Views | covered | source: tests/test_tree.py::test_walk |
| oracle/test_rendering.py::test_no_end_newline_empty_h1 | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[#-<h1></h1>\n] |
| oracle/test_rendering.py::test_no_end_newline_empty_h3 | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[###-<h3></h3>\n] |
| oracle/test_rendering.py::test_no_end_newline_inline_code_space | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[` `-<p><code> </code></p>\n] |
| oracle/test_rendering.py::test_no_end_newline_empty_fence | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[``````-<pre><code></code></pre>\n] |
| oracle/test_rendering.py::test_no_end_newline_empty_unordered_item | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[--<ul>\n<li></li>\n</ul>\n] |
| oracle/test_rendering.py::test_no_end_newline_empty_ordered_item | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[1.-<ol>\n<li></li>\n</ol>\n] |
| oracle/test_rendering.py::test_no_end_newline_empty_blockquote | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[>-<blockquote></blockquote>\n] |
| oracle/test_rendering.py::test_no_end_newline_horizontal_rule | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[----<hr />\n] |
| oracle/test_rendering.py::test_no_end_newline_html_block | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[<h1></h1>-<h1></h1>] |
| oracle/test_rendering.py::test_no_end_newline_paragraph | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[p-<p>p</p>\n] |
| oracle/test_rendering.py::test_no_end_newline_reference_definition | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[[reference]: /url-] |
| oracle/test_rendering.py::test_no_end_newline_indented_code | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[    indented code block-<pre><code>indented code block\n</code></pre>\n] |
| oracle/test_rendering.py::test_no_end_newline_blockquote_after_text | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_no_end_newline.py::test_no_end_newline[> test\n>-<blockquote>\n<p>test</p>\n</blockquote>\n] |
| oracle/test_references.py::test_ref_definitions | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_references.py::test_ref_definitions |
| oracle/test_misc.py::test_highlight_arguments | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_misc.py::test_highlight_arguments |
| oracle/test_misc.py::test_ordered_list_info | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_port/test_misc.py::test_ordered_list_info |
| oracle/test_commonmark.py::test_commonmark_tab_example_1 | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_cmark_spec/test_spec.py::test_spec[entry0] |
| oracle/test_commonmark.py::test_commonmark_tab_example_2 | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_cmark_spec/test_spec.py::test_spec[entry1] |
| oracle/test_commonmark.py::test_commonmark_tab_example_3 | upstream_rewritten | integration | Markdown Rendering Behavior | covered | source: tests/test_cmark_spec/test_spec.py::test_spec[entry2] |

Total: 81 | kept: 81 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 81
