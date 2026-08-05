# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_new_font_exposes_expected_table_tags` | atomic | Table Projection | covered |
| 2 | `oracle/test_atomic.py::test_glyph_order_preserves_builder_sequence` | atomic | Font Construction Projection | covered |
| 3 | `oracle/test_atomic.py::test_character_map_projects_unicode_to_glyph_names` | atomic | Character Map Projection | covered |
| 4 | `oracle/test_atomic.py::test_cmap_uses_format_twelve_for_non_bmp_codepoint` | atomic | Character Map Projection | covered |
| 5 | `oracle/test_atomic.py::test_horizontal_metrics_are_rounded_and_accessible` | atomic | Table Projection | covered |
| 6 | `oracle/test_atomic.py::test_name_table_returns_expected_english_strings` | atomic | Table Projection | covered |
| 7 | `oracle/test_atomic.py::test_head_table_uses_configured_units_per_em` | atomic | Table Projection | covered |
| 8 | `oracle/test_atomic.py::test_hhea_table_keeps_configured_vertical_extents` | atomic | Table Projection | covered |
| 9 | `oracle/test_atomic.py::test_os2_table_keeps_vendor_and_windows_extents` | atomic | Table Projection | covered |
| 10 | `oracle/test_atomic.py::test_glyf_table_contains_simple_and_component_glyphs` | atomic | Glyph And Pen Projection | covered |
| 11 | `oracle/test_atomic.py::test_glyph_bounds_are_calculated_from_contours` | atomic | Glyph And Pen Projection | covered |
| 12 | `oracle/test_atomic.py::test_get_glyph_set_exposes_metrics_and_bounds` | atomic | Glyph And Pen Projection | covered |
| 13 | `oracle/test_atomic.py::test_bounds_pen_calculates_drawn_glyph_bounds` | atomic | Glyph And Pen Projection | covered |
| 14 | `oracle/test_atomic.py::test_recording_pen_captures_public_pen_protocol` | atomic | Glyph And Pen Projection | covered |
| 15 | `oracle/test_atomic.py::test_tt_glyph_pen_builds_quadratic_glyph` | atomic | Glyph And Pen Projection | covered |
| 16 | `oracle/test_atomic.py::test_font_builder_rejects_cubic_glyf_by_default` | atomic | Font Construction Projection | covered |
| 17 | `oracle/test_atomic.py::test_font_bytes_can_reload_with_ttfont` | atomic | Binary Font Projection | covered |
| 18 | `oracle/test_atomic.py::test_save_xml_can_emit_selected_tables` | atomic | TTX XML Projection | covered |
| 19 | `oracle/test_atomic.py::test_new_table_can_create_and_attach_meta_table` | atomic | Table Projection | covered |
| 20 | `oracle/test_atomic.py::test_sorted_tag_list_orders_font_tables` | atomic | Table Projection | covered |
| 21 | `oracle/test_atomic.py::test_xml_tag_conversion_round_trips_public_tag` | atomic | TTX XML Projection | covered |
| 22 | `oracle/test_atomic.py::test_reorder_font_tables_moves_glyph_order_first` | atomic | Table Projection | covered |
| 23 | `oracle/test_atomic.py::test_subset_options_default_to_recommended_glyph_names` | atomic | Subset Projection | covered |
| 24 | `oracle/test_atomic.py::test_subsetter_populate_records_unicode_and_glyph_requests` | atomic | Subset Projection | covered |
| 25 | `oracle/test_atomic.py::test_ttfont_set_glyph_order_updates_ordered_projection` | atomic | Font Construction Projection | covered |
| 26 | `oracle/test_atomic.py::test_get_best_cmap_prefers_unicode_mapping` | atomic | Character Map Projection | covered |
| 27 | `oracle/test_atomic.py::test_ttfont_round_trip_stream_keeps_metrics` | atomic | Table Projection | covered |
| 28 | `oracle/test_atomic.py::test_xml_writer_includes_fonttools_root_element` | atomic | TTX XML Projection | covered |
| 29 | `oracle/test_atomic.py::test_ttfont_import_xml_accepts_generated_selected_table` | atomic | TTX XML Projection | covered |
| 30 | `oracle/test_atomic.py::test_font_save_to_bytes_produces_sfnt_header` | atomic | Table Projection | covered |
| 31 | `oracle/test_integration.py::test_saved_font_reloads_same_glyph_order_and_table_set` | integration | Table Projection | covered |
| 32 | `oracle/test_integration.py::test_saved_font_reloads_same_best_cmap` | integration | Character Map Projection | covered |
| 33 | `oracle/test_integration.py::test_saved_font_reloads_same_horizontal_metrics` | integration | Table Projection | covered |
| 34 | `oracle/test_integration.py::test_saved_font_reloads_name_strings` | integration | Binary Font Projection | covered |
| 35 | `oracle/test_integration.py::test_xml_export_import_preserves_head_units` | integration | TTX XML Projection | covered |
| 36 | `oracle/test_integration.py::test_xml_export_import_preserves_name_table` | integration | TTX XML Projection | covered |
| 37 | `oracle/test_integration.py::test_glyph_set_draw_bounds_match_glyf_bounds` | integration | Glyph And Pen Projection | covered |
| 38 | `oracle/test_integration.py::test_component_glyph_draw_records_component_references` | integration | Glyph And Pen Projection | covered |
| 39 | `oracle/test_integration.py::test_subsetter_reduces_font_to_requested_text_and_components` | integration | Subset Projection | covered |
| 40 | `oracle/test_integration.py::test_subsetter_keeps_component_dependencies_for_aacute` | integration | Subset Projection | covered |
| 41 | `oracle/test_integration.py::test_subset_font_saves_and_reloads_with_filtered_cmap` | integration | Subset Projection | covered |
| 42 | `oracle/test_integration.py::test_added_meta_table_survives_binary_round_trip` | integration | Table Projection | covered |
| 43 | `oracle/test_integration.py::test_sorted_table_projection_contains_same_tags_after_reload` | integration | Table Projection | covered |
| 44 | `oracle/test_integration.py::test_xml_tag_conversion_matches_emitted_table_name` | integration | TTX XML Projection | covered |
| 45 | `oracle/test_integration.py::test_text_subset_only_retains_requested_unicode_mapping` | integration | Subset Projection | covered |
| 46 | `oracle/test_integration.py::test_reloaded_glyph_bounds_match_original` | integration | Glyph And Pen Projection | covered |
| 47 | `oracle/test_integration.py::test_imported_xml_table_can_be_saved_with_generated_font` | integration | TTX XML Projection | covered |
| 48 | `oracle/test_integration.py::test_glyph_order_change_preserves_existing_cmap_names` | integration | Character Map Projection | covered |
| 49 | `oracle/test_integration.py::test_added_pen_glyph_can_be_addressed_through_glyph_set` | integration | Glyph And Pen Projection | covered |
| 50 | `oracle/test_integration.py::test_vertical_metric_tables_remain_consistent_after_reload` | integration | Table Projection | covered |
| 51 | `oracle/test_integration.py::test_binary_to_xml_to_binary_preserves_name_projection` | integration | TTX XML Projection | covered |
| 52 | `oracle/test_integration.py::test_subset_options_can_retain_requested_name_records` | integration | Subset Projection | covered |
| 53 | `oracle/test_integration.py::test_subset_component_glyph_draws_after_dependency_closure` | integration | Subset Projection | covered |
| 54 | `oracle/test_integration.py::test_meta_table_can_be_exported_after_binary_reload` | integration | Table Projection | covered |
| 55 | `oracle/test_integration.py::test_non_bmp_subset_retains_format_twelve_mapping` | integration | Subset Projection | covered |
| 56 | `oracle/test_integration.py::test_reordered_glyph_order_survives_binary_round_trip` | integration | Binary Font Projection | covered |
| 57 | `oracle/test_integration.py::test_component_data_survives_binary_round_trip` | integration | Glyph And Pen Projection | covered |
| 58 | `oracle/test_integration.py::test_glyph_name_subset_keeps_component_closure_after_reload` | integration | Subset Projection | covered |
| 59 | `oracle/test_integration.py::test_xml_export_import_preserves_horizontal_metric_tables` | integration | TTX XML Projection | covered |
| 60 | `oracle/test_integration.py::test_subset_glyph_remains_drawable_with_original_metrics` | integration | Subset Projection | covered |

final_scoreable: 60
