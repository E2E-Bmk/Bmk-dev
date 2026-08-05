# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_app_key_event_receives_pilot_press_character` | atomic | Scope | covered |
| 2 | `oracle/test_atomic.py::test_run_test_exposes_pilot_and_mounts_input` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_input_press_updates_value_and_emits_changed` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_input_cursor_and_selection_follow_arrow_keys` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_input_submit_emits_submitted_message` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_input_blur_emits_blurred_message_when_focus_moves` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_input_restrict_and_max_length_block_invalid_replacement` | atomic | Error Semantics | covered |
| 8 | `oracle/test_atomic.py::test_input_selection_and_delete_programmatic_helpers` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_datatable_add_columns_and_rows_preserve_order` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_datatable_row_and_column_keys_round_trip` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_datatable_update_cell_and_coordinate_lookup_round_trip` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_datatable_sort_changes_coordinate_projection` | atomic | Cross-Component Invariants | covered |
| 13 | `oracle/test_atomic.py::test_datatable_cell_cursor_highlight_and_select_messages` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_datatable_row_cursor_highlight_and_select_messages` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_datatable_column_cursor_highlight_and_select_messages` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_datatable_header_click_emits_header_selected` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_datatable_row_label_click_emits_row_label_selected` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_tree_root_and_added_nodes_have_parent_links` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_tree_expand_and_collapse_messages_are_public` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_tree_keyboard_selection_and_auto_expand_messages` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_tree_clear_resets_root_and_cursor` | atomic | Error Semantics | covered |
| 22 | `oracle/test_atomic.py::test_tabs_empty_and_populated_states_are_distinct` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_tabs_clicking_a_tab_changes_active_tab` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_tabs_keyboard_navigation_wraps_across_edges` | atomic | Product State Model | covered |
| 25 | `oracle/test_atomic.py::test_tabs_hide_show_disable_enable_emit_public_messages` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_css_layout_projects_widget_regions` | atomic | Cross-Component Invariants | covered |
| 27 | `oracle/test_atomic.py::test_css_style_projection_sets_expected_widget_sizes` | atomic | Cross-Component Invariants | covered |
| 28 | `oracle/test_atomic.py::test_input_home_and_end_actions_update_cursor_position` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_datatable_clear_rows_preserves_public_columns` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_tree_add_leaf_and_remove_preserve_parent_projection` | atomic | Product State Model | covered |
| 31 | `oracle/test_integration.py::test_input_edit_submit_and_blur_workflow` | integration | Representative Workflow | covered |
| 32 | `oracle/test_integration.py::test_input_click_selection_delete_and_retype_workflow` | integration | Representative Workflow | covered |
| 33 | `oracle/test_integration.py::test_input_restrict_submit_and_blur_workflow` | integration | Representative Workflow | covered |
| 34 | `oracle/test_integration.py::test_datatable_add_update_sort_and_coordinate_workflow` | integration | Representative Workflow | covered |
| 35 | `oracle/test_integration.py::test_datatable_click_then_sort_keeps_row_identity_workflow` | integration | Cross-Component Invariants | covered |
| 36 | `oracle/test_integration.py::test_datatable_row_and_column_cursor_workflow` | integration | Representative Workflow | covered |
| 37 | `oracle/test_integration.py::test_datatable_header_and_row_label_workflow` | integration | Representative Workflow | covered |
| 38 | `oracle/test_integration.py::test_tree_expand_select_collapse_workflow` | integration | Representative Workflow | covered |
| 39 | `oracle/test_integration.py::test_tree_move_cursor_and_reset_workflow` | integration | Representative Workflow | covered |
| 40 | `oracle/test_integration.py::test_tree_clear_and_repopulate_workflow` | integration | Representative Workflow | covered |
| 41 | `oracle/test_integration.py::test_tabs_add_navigate_and_remove_workflow` | integration | Representative Workflow | covered |
| 42 | `oracle/test_integration.py::test_tabs_hide_show_disable_enable_workflow` | integration | Representative Workflow | covered |
| 43 | `oracle/test_integration.py::test_tabs_mouse_and_keyboard_navigation_share_active_state` | integration | Cross-Component Invariants | covered |
| 44 | `oracle/test_integration.py::test_tabs_clear_and_readd_workflow` | integration | Representative Workflow | covered |
| 45 | `oracle/test_integration.py::test_layout_regions_remain_stable_after_interactions` | integration | Cross-Component Invariants | covered |
| 46 | `oracle/test_integration.py::test_combined_input_submit_tab_click_and_table_selection_workflow` | integration | Representative Workflow | covered |
| 47 | `oracle/test_integration.py::test_combined_tree_and_table_selection_messages_share_one_app_log` | integration | Cross-Component Invariants | covered |
| 48 | `oracle/test_integration.py::test_combined_tab_click_blurs_input_and_keeps_layout_projections` | integration | Cross-Component Invariants | covered |
| 49 | `oracle/test_integration.py::test_combined_dashboard_rebuilds_table_and_tree_from_input_submission` | integration | Representative Workflow | covered |
| 50 | `oracle/test_integration.py::test_app_key_event_and_widget_messages_can_coexist_in_one_workflow` | integration | Cross-Component Invariants | covered |
| 51 | `oracle/test_integration.py::test_pilot_clicking_multiple_widgets_preserves_event_order` | integration | Cross-Component Invariants | covered |
| 52 | `oracle/test_integration.py::test_datatable_remove_row_and_column_after_selection_workflow` | integration | Representative Workflow | covered |
| 53 | `oracle/test_integration.py::test_tabs_remove_active_and_clear_message_workflow` | integration | Representative Workflow | covered |
| 54 | `oracle/test_integration.py::test_tree_show_root_and_keyboard_navigation_workflow` | integration | Representative Workflow | covered |
| 55 | `oracle/test_integration.py::test_input_home_selection_and_replacement_workflow` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_datatable_clear_rebuild_and_sort_workflow` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_tree_nested_add_remove_and_cursor_workflow` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_tabs_relabel_and_programmatic_activation_workflow` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_table_and_tree_rebuild_keep_shared_item_identity` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_dashboard_reset_workflow_keeps_widget_regions_stable` | integration | Cross-View Invariants | covered |

final_scoreable: 60
