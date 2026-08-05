# Behavior Map

Each physical check below is covered by the corresponding public behavior section.

| Layer | Test | Scope section | Coverage |
| --- | --- | --- | --- |
| atomic | test_public_import_surface_exposes_core_modules | Scope | covered |
| atomic | test_keyboard_event_projects_code_and_text | Product State Model | covered |
| atomic | test_mouse_event_projects_coordinates_and_flags | Product State Model | covered |
| atomic | test_scene_projects_name_duration_clear_and_effects | Product State Model | covered |
| atomic | test_scene_add_and_remove_effect_updates_registration | Product State Model | covered |
| atomic | test_scene_sends_events_in_reverse_effect_order | Product State Model | covered |
| atomic | test_effect_updates_only_inside_configured_frame_window | Product State Model | covered |
| atomic | test_effect_reset_delete_count_and_default_properties | Product State Model | covered |
| atomic | test_path_jump_and_wait_replays_positions | Product State Model | covered |
| atomic | test_path_straight_motion_reaches_endpoint | Product State Model | covered |
| atomic | test_path_round_motion_is_repeatable_after_reset | Product State Model | covered |
| atomic | test_dynamic_path_starts_at_configured_position_and_moves_on_event | Product State Model | covered |
| atomic | test_static_renderer_projects_dimensions_and_images | Product State Model | covered |
| atomic | test_static_renderer_animation_and_reset_are_public | Product State Model | covered |
| atomic | test_static_renderer_projects_colour_sequences_without_ansi_snapshot | Product State Model | covered |
| atomic | test_print_effect_uses_renderer_projection_and_screen_paint | Product State Model | covered |
| atomic | test_print_effect_speed_gates_repaints | Product State Model | covered |
| atomic | test_wipe_effect_advances_on_even_frames | Product State Model | covered |
| atomic | test_scroll_effect_uses_configured_rate | Product State Model | covered |
| atomic | test_sprite_follows_path_and_records_last_position | Product State Model | covered |
| atomic | test_sprite_overlap_uses_last_positions | Product State Model | covered |
| atomic | test_sprite_forwards_events_to_dynamic_paths | Product State Model | covered |
| atomic | test_widget_constants_and_label_value_contract | Cross-Component Invariants | covered |
| atomic | test_button_keyboard_event_invokes_callback | Product State Model | covered |
| atomic | test_checkbox_toggle_and_callback | Cross-Component Invariants | covered |
| atomic | test_radio_buttons_navigation_and_value_selection | Cross-Component Invariants | covered |
| atomic | test_text_editing_and_validator_state | Cross-Component Invariants | covered |
| atomic | test_textbox_multiline_value_and_enter_transition | Cross-Component Invariants | covered |
| atomic | test_dropdown_value_and_options_projection | Cross-Component Invariants | covered |
| atomic | test_listbox_selection_and_start_line_projection | Cross-Component Invariants | covered |
| atomic | test_layout_focus_and_find_widget | Cross-Component Invariants | covered |
| atomic | test_frame_data_round_trip_with_named_widgets | Cross-Component Invariants | covered |
| atomic | test_frame_theme_and_title_are_public | Cross-Component Invariants | covered |
| atomic | test_frame_update_flushes_canvas_to_recording_screen | Product State Model | covered |
| atomic | test_canvas_location_and_visibility_are_stable | Product State Model | covered |
| atomic | test_screen_control_and_key_constants_are_deterministic | Product State Model | covered |
| integration | test_scene_event_workflow_preserves_unhandled_event | Product State Model | covered |
| integration | test_path_and_sprite_workflow_draws_each_position | Product State Model | covered |
| integration | test_print_and_wipe_compose_over_one_recording_screen | Product State Model | covered |
| integration | test_scene_update_workflow_runs_background_and_scroll_effects | Product State Model | covered |
| integration | test_renderer_reset_and_effect_speed_form_a_repeatable_workflow | Product State Model | covered |
| integration | test_dynamic_sprite_event_then_render_workflow | Product State Model | covered |
| integration | test_button_and_checkbox_form_workflow_records_actions | Cross-Component Invariants | covered |
| integration | test_radio_and_text_workflow_combines_selection_and_validation | Cross-Component Invariants | covered |
| integration | test_textbox_frame_save_workflow_persists_multiline_content | Cross-Component Invariants | covered |
| integration | test_listbox_and_label_workflow_tracks_selected_record | Cross-Component Invariants | covered |
| integration | test_dropdown_options_and_layout_lookup_workflow | Cross-Component Invariants | covered |
| integration | test_layout_focus_then_frame_render_workflow | Cross-Component Invariants | covered |
| integration | test_frame_initial_data_updates_text_and_checkbox_widgets | Cross-Component Invariants | covered |
| integration | test_frame_theme_title_and_render_workflow | Cross-Component Invariants | covered |
| integration | test_frame_child_effect_and_frame_render_workflow | Product State Model | covered |
| integration | test_print_clear_delete_workflow_replaces_previous_projection | Product State Model | covered |
| integration | test_two_sprite_motion_workflow_rechecks_overlap_after_updates | Product State Model | covered |
| integration | test_path_reset_workflow_replays_same_route | Product State Model | covered |
| integration | test_scene_exit_workflow_saves_effect_state | Product State Model | covered |
| integration | test_scene_topmost_button_like_effect_swallow_workflow | Product State Model | covered |
| integration | test_animated_renderer_print_workflow_cycles_images | Product State Model | covered |
| integration | test_canvas_and_renderer_dimensions_drive_a_print_position | Product State Model | covered |
| integration | test_coloured_renderer_print_workflow_keeps_colour_map_shape | Product State Model | covered |
| integration | test_checkbox_radio_callback_workflow_tracks_form_state | Cross-Component Invariants | covered |
| integration | test_text_validation_and_render_workflow_exposes_current_value | Cross-Component Invariants | covered |
| integration | test_textbox_edit_and_render_workflow | Cross-Component Invariants | covered |
| integration | test_listbox_keyboard_and_render_workflow | Product State Model | covered |
| integration | test_complete_form_workflow_edits_saves_and_renders | Scope | covered |
| integration | test_selection_form_workflow_updates_dropdown_and_renders | Cross-Component Invariants | covered |
| integration | test_scene_composes_effect_and_widget_frame_workflow | Product State Model | covered |
| integration | test_control_key_and_text_edit_workflow_uses_public_constants | Product State Model | covered |
| integration | test_background_scene_lifecycle_workflow_is_local_and_repeatable | Product State Model | covered |

final_scoreable: 68
