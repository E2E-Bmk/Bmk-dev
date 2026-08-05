# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_exposes_workbook_and_version` | atomic | Installable Surface | covered |
| 2 | `oracle/test_atomic.py::test_workbook_closes_to_a_zip_stream` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_add_worksheet_projects_names_in_workbook_xml` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_get_worksheet_by_name_returns_the_public_sheet_object` | atomic | Installable Surface | covered |
| 5 | `oracle/test_atomic.py::test_add_format_bold_and_number_format_reach_styles_xml` | atomic | Cross-View Invariants | covered |
| 6 | `oracle/test_atomic.py::test_write_string_projects_shared_string_cell` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_write_number_projects_numeric_value` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_write_boolean_projects_boolean_cell_type` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_write_datetime_projects_excel_serial_and_format` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_write_formula_projects_formula_and_cached_value` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_write_array_formula_projects_range_reference` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_write_dynamic_array_formula_projects_dynamic_marker` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_write_rich_string_projects_multiple_runs` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_write_row_projects_mixed_values_across_columns` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_write_column_projects_values_down_rows` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_write_blank_with_format_projects_style_only_cell` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_set_column_projects_width_and_custom_width` | atomic | Cross-View Invariants | covered |
| 18 | `oracle/test_atomic.py::test_set_row_projects_height_and_hidden_state` | atomic | Cross-View Invariants | covered |
| 19 | `oracle/test_atomic.py::test_freeze_panes_projects_frozen_view` | atomic | Cross-View Invariants | covered |
| 20 | `oracle/test_atomic.py::test_merge_range_projects_merge_cell_ref` | atomic | Cross-View Invariants | covered |
| 21 | `oracle/test_atomic.py::test_autofilter_projects_filter_range` | atomic | Cross-View Invariants | covered |
| 22 | `oracle/test_atomic.py::test_define_name_projects_global_and_local_names` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_add_table_projects_table_part_and_reference` | atomic | Cross-View Invariants | covered |
| 24 | `oracle/test_atomic.py::test_write_external_url_projects_hyperlink_relationship` | atomic | Cross-View Invariants | covered |
| 25 | `oracle/test_atomic.py::test_write_internal_url_projects_location_without_external_target` | atomic | Cross-View Invariants | covered |
| 26 | `oracle/test_atomic.py::test_write_comment_projects_comment_author_and_cell_ref` | atomic | Cross-View Invariants | covered |
| 27 | `oracle/test_atomic.py::test_insert_chart_projects_chart_xml_and_drawing_relationship` | atomic | Cross-View Invariants | covered |
| 28 | `oracle/test_atomic.py::test_set_properties_projects_title_without_asserting_timestamps` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_set_calc_mode_projects_calculation_policy` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_write_fraction_projects_as_numeric_value` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_workbook_projection_has_stable_required_parts` | atomic | Cross-View Invariants | covered |
| 32 | `oracle/test_integration.py::test_named_sheets_and_strings_form_a_workbook_workflow` | integration | Representative Workflow | covered |
| 33 | `oracle/test_integration.py::test_scalar_cells_and_formula_project_together` | integration | Representative Workflow | covered |
| 34 | `oracle/test_integration.py::test_formatted_datetime_and_numeric_cells_share_style_projection` | integration | Cross-View Invariants | covered |
| 35 | `oracle/test_integration.py::test_column_data_and_boolean_flag_form_rows` | integration | Representative Workflow | covered |
| 36 | `oracle/test_integration.py::test_rich_and_plain_strings_keep_distinct_shared_string_entries` | integration | Cross-View Invariants | covered |
| 37 | `oracle/test_integration.py::test_array_and_scalar_formula_ranges_remain_separate` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_dynamic_formula_and_source_number_form_spill_projection` | integration | Representative Workflow | covered |
| 39 | `oracle/test_integration.py::test_row_and_column_writes_build_a_rectangular_data_block` | integration | Representative Workflow | covered |
| 40 | `oracle/test_integration.py::test_blank_format_and_column_width_preserve_layout_metadata` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_hidden_rows_and_frozen_header_form_view_state` | integration | Representative Workflow | covered |
| 42 | `oracle/test_integration.py::test_merged_label_and_cell_projection_form_one_section` | integration | Representative Workflow | covered |
| 43 | `oracle/test_integration.py::test_header_row_and_autofilter_form_filterable_data` | integration | Representative Workflow | covered |
| 44 | `oracle/test_integration.py::test_global_and_local_names_track_two_sheet_workflow` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_table_data_and_table_part_reference_same_range` | integration | Representative Workflow | covered |
| 46 | `oracle/test_integration.py::test_table_and_comment_parts_have_distinct_relationship_types` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_external_and_internal_hyperlinks_use_different_projections` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_comment_author_and_core_author_are_independent_metadata` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_chart_series_cache_projects_written_numeric_source` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_chart_and_defined_name_parts_coexist_in_package` | integration | Representative Workflow | covered |
| 51 | `oracle/test_integration.py::test_manual_calc_mode_and_formula_cache_form_recalculation_workflow` | integration | Representative Workflow | covered |
| 52 | `oracle/test_integration.py::test_two_identical_sheet_builds_have_same_structural_member_set` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_date_cell_and_properties_keep_timestamp_sensitive_fields_out_of_projection` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_numeric_fraction_and_formula_values_share_numeric_cell_contract` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_row_and_column_layout_settings_survive_with_written_cells` | integration | Representative Workflow | covered |
| 56 | `oracle/test_integration.py::test_merged_title_and_table_form_non_overlapping_structural_parts` | integration | Representative Workflow | covered |
| 57 | `oracle/test_integration.py::test_linked_and_annotated_cell_has_both_sheet_and_relationship_projections` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_chart_anchor_and_column_layout_form_dashboard_structure` | integration | Representative Workflow | covered |
| 59 | `oracle/test_integration.py::test_table_and_name_refer_to_different_public_workbook_ranges` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_sheet_lookup_and_written_content_form_named_sheet_workflow` | integration | Representative Workflow | covered |
| 61 | `oracle/test_integration.py::test_internal_navigation_and_merged_heading_form_local_workflow` | integration | Representative Workflow | covered |
| 62 | `oracle/test_integration.py::test_public_workbook_import_and_close_support_repeated_local_runs` | integration | Representative Workflow | covered |
| 63 | `oracle/test_integration.py::test_workbook_policy_and_properties_are_present_together` | integration | Product State Model | covered |
| 64 | `oracle/test_integration.py::test_formula_summary_and_table_detail_are_separate_parts` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_filterable_frozen_data_sheet_forms_a_multi_view_workflow` | integration | Representative Workflow | covered |
| 66 | `oracle/test_integration.py::test_rich_caption_and_chart_form_visual_report_parts` | integration | Representative Workflow | covered |

final_scoreable: 66
