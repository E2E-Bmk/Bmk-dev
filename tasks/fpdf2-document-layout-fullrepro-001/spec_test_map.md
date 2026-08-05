# Specification To Test Map

Each physical test below is covered by the public behavior specification.

| Physical nodeid | Layer | Contract area | Status |
| --- | --- | --- | --- |
| `oracle/test_atomic.py::test_default_document_geometry_and_margins` | atomic | default geometry | covered |
| `oracle/test_atomic.py::test_custom_unit_and_format_geometry` | atomic | custom geometry | covered |
| `oracle/test_atomic.py::test_orientation_changes_page_dimensions` | atomic | orientation | covered |
| `oracle/test_atomic.py::test_add_page_initializes_page_and_position` | atomic | page initialization | covered |
| `oracle/test_atomic.py::test_multiple_pages_track_count_and_page_no` | atomic | page inventory | covered |
| `oracle/test_atomic.py::test_set_margins_updates_effective_area_and_position` | atomic | margins | covered |
| `oracle/test_atomic.py::test_set_individual_margins_updates_state` | atomic | margin controls | covered |
| `oracle/test_atomic.py::test_auto_page_break_controls_trigger` | atomic | page breaks | covered |
| `oracle/test_atomic.py::test_set_xy_and_ln_update_coordinates` | atomic | coordinates | covered |
| `oracle/test_atomic.py::test_set_font_selects_builtin_font_and_size` | atomic | fonts | covered |
| `oracle/test_atomic.py::test_builtin_font_name_is_case_insensitive` | atomic | font names | covered |
| `oracle/test_atomic.py::test_string_width_is_positive_and_size_sensitive` | atomic | font metrics | covered |
| `oracle/test_atomic.py::test_text_emits_literal_content` | atomic | text output | covered |
| `oracle/test_atomic.py::test_cell_moves_to_requested_coordinates` | atomic | cells | covered |
| `oracle/test_atomic.py::test_cell_border_and_fill_emit_drawing_commands` | atomic | cell styling | covered |
| `oracle/test_atomic.py::test_multi_cell_wraps_and_returns_to_margin` | atomic | multi-cell | covered |
| `oracle/test_atomic.py::test_multi_cell_dry_run_reports_lines_without_writing` | atomic | dry-run layout | covered |
| `oracle/test_atomic.py::test_multi_cell_new_x_new_y_controls_position` | atomic | position controls | covered |
| `oracle/test_atomic.py::test_write_advances_vertical_position` | atomic | writing | covered |
| `oracle/test_atomic.py::test_line_and_rect_emit_path_operators` | atomic | drawing | covered |
| `oracle/test_atomic.py::test_color_setters_change_graphics_state` | atomic | colors | covered |
| `oracle/test_atomic.py::test_external_link_adds_annotation` | atomic | external links | covered |
| `oracle/test_atomic.py::test_link_method_accepts_alt_text` | atomic | link descriptions | covered |
| `oracle/test_atomic.py::test_internal_link_targets_page` | atomic | internal links | covered |
| `oracle/test_atomic.py::test_named_destination_can_be_referenced` | atomic | named destinations | covered |
| `oracle/test_atomic.py::test_metadata_fields_appear_in_info_dictionary` | atomic | metadata | covered |
| `oracle/test_atomic.py::test_creation_date_can_be_set_deterministically` | atomic | creation date | covered |
| `oracle/test_atomic.py::test_alias_nb_pages_is_substituted_on_output` | atomic | page aliases | covered |
| `oracle/test_atomic.py::test_start_section_records_outline` | atomic | outlines | covered |
| `oracle/test_atomic.py::test_invalid_outline_level_raises_value_error` | atomic | outline validation | covered |
| `oracle/test_atomic.py::test_table_context_renders_rows_and_headers` | atomic | tables | covered |
| `oracle/test_atomic.py::test_fontface_context_changes_and_restores_font` | atomic | font contexts | covered |
| `oracle/test_integration.py::test_margin_font_cell_workflow_emits_one_page` | integration | layout workflow | covered |
| `oracle/test_integration.py::test_mixed_orientation_pages_preserve_page_inventory` | integration | page workflow | covered |
| `oracle/test_integration.py::test_precise_drawing_workflow_contains_text_and_shapes` | integration | drawing workflow | covered |
| `oracle/test_integration.py::test_wrapped_content_workflow_triggers_predictable_page_break` | integration | break workflow | covered |
| `oracle/test_integration.py::test_write_workflow_uses_font_metrics_and_preserves_content` | integration | text workflow | covered |
| `oracle/test_integration.py::test_dry_run_then_render_workflow_matches_planned_lines` | integration | planning workflow | covered |
| `oracle/test_integration.py::test_colored_filled_cell_workflow_keeps_stable_geometry` | integration | style workflow | covered |
| `oracle/test_integration.py::test_external_link_workflow_combines_text_and_rectangle_annotations` | integration | link workflow | covered |
| `oracle/test_integration.py::test_internal_link_workflow_jumps_from_summary_to_detail` | integration | page link workflow | covered |
| `oracle/test_integration.py::test_named_destination_workflow_links_labeled_sections` | integration | named link workflow | covered |
| `oracle/test_integration.py::test_metadata_workflow_emits_stable_information_dictionary` | integration | metadata workflow | covered |
| `oracle/test_integration.py::test_page_alias_workflow_reports_final_page_count` | integration | alias workflow | covered |
| `oracle/test_integration.py::test_outline_workflow_emits_nested_bookmark_titles` | integration | outline workflow | covered |
| `oracle/test_integration.py::test_styled_heading_workflow_renders_outline_and_visible_heading` | integration | heading workflow | covered |
| `oracle/test_integration.py::test_table_workflow_renders_headers_rows_and_borders` | integration | table workflow | covered |
| `oracle/test_integration.py::test_multiline_table_workflow_preserves_wrapped_cell_content` | integration | wrapped table | covered |
| `oracle/test_integration.py::test_long_table_workflow_can_span_pages_without_losing_rows` | integration | paginated table | covered |
| `oracle/test_integration.py::test_wrapping_write_workflow_finishes_with_page_alias` | integration | paginated writing | covered |
| `oracle/test_integration.py::test_linked_cell_sequence_keeps_content_order_and_annotation` | integration | linked cells | covered |
| `oracle/test_integration.py::test_output_workflow_closes_buffer_and_preserves_page_count` | integration | output lifecycle | covered |
| `oracle/test_integration.py::test_margin_reset_workflow_repositions_wrapped_content` | integration | margin workflow | covered |
| `oracle/test_integration.py::test_drawing_style_workflow_combines_colors_lines_and_rectangles` | integration | styled drawing | covered |
| `oracle/test_integration.py::test_report_workflow_combines_metadata_outline_table_and_link` | integration | report workflow | covered |
| `oracle/test_integration.py::test_custom_page_workflow_uses_geometry_for_wrapping` | integration | custom-page workflow | covered |
| `oracle/test_integration.py::test_outline_recovery_workflow_rejects_gap_then_continues` | integration | outline recovery | covered |
| `oracle/test_integration.py::test_font_context_workflow_switches_builtin_styles_and_restores` | integration | font workflow | covered |
| `oracle/test_integration.py::test_page_state_workflow_outputs_each_page_content` | integration | page state | covered |
| `oracle/test_integration.py::test_linked_dated_document_workflow_combines_page_and_info_views` | integration | linked metadata | covered |

final_scoreable: 60
