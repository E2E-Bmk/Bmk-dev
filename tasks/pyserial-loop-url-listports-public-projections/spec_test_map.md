# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_public_import_surface_exposes_version_and_protocol_packages` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_serial_constants_describe_supported_configuration_values` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_serial_without_port_is_closed_and_named_none` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_serial_constructor_projects_configuration_properties` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_port_property_accepts_string_and_none` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_baudrate_property_accepts_integer_configuration` | atomic | Product State Model | covered |
| 7 | `oracle/test_atomic.py::test_bytesize_property_accepts_documented_value` | atomic | Product State Model | covered |
| 8 | `oracle/test_atomic.py::test_parity_property_accepts_documented_values` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_stopbits_property_accepts_documented_values` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_timeout_property_accepts_none_zero_and_float` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_write_timeout_property_accepts_none_zero_and_float` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_inter_byte_timeout_property_accepts_none_zero_and_float` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_flow_control_properties_project_boolean_values` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_dsrdtr_none_follows_rtscts_publicly` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_invalid_configuration_values_raise_value_error` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_get_settings_exposes_documented_serial_settings` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_apply_settings_updates_public_serial_settings` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_serial_context_manager_closes_loop_url` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_serial_for_url_selects_loop_handler` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_serial_for_url_can_defer_opening` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_unknown_url_protocol_raises_value_error` | atomic | Product State Model | covered |
| 22 | `oracle/test_atomic.py::test_loop_url_accepts_documented_logging_option` | atomic | Product State Model | covered |
| 23 | `oracle/test_atomic.py::test_loop_url_starts_open_and_reports_public_name` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_loop_write_returns_byte_count` | atomic | Product State Model | covered |
| 25 | `oracle/test_atomic.py::test_loop_in_waiting_counts_written_bytes` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_loop_read_returns_written_bytes` | atomic | Product State Model | covered |
| 27 | `oracle/test_atomic.py::test_loop_read_all_drains_available_bytes` | atomic | Product State Model | covered |
| 28 | `oracle/test_atomic.py::test_loop_read_until_includes_expected_terminator` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_loop_reset_input_buffer_discards_available_bytes` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_closed_loop_operations_raise_port_not_open_error` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_list_port_info_initializes_public_metadata_defaults` | atomic | Product State Model | covered |
| 32 | `oracle/test_atomic.py::test_list_port_info_projects_runner_created_metadata` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_list_port_info_usb_description_uses_product_and_interface` | atomic | Product State Model | covered |
| 34 | `oracle/test_atomic.py::test_list_port_info_usb_info_projects_identifiers` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_list_port_info_supports_legacy_index_projection` | atomic | Product State Model | covered |
| 36 | `oracle/test_atomic.py::test_list_port_info_natural_order_and_equality_are_public` | atomic | Product State Model | covered |
| 37 | `oracle/test_integration.py::test_settings_round_trip_updates_a_closed_serial` | integration | Cross-View Invariants | covered |
| 38 | `oracle/test_integration.py::test_url_configuration_and_loop_transfer_form_one_workflow` | integration | Cross-View Invariants | covered |
| 39 | `oracle/test_integration.py::test_deferred_url_open_then_write_and_read` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_context_workflow_writes_reads_and_closes` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_buffer_projection_progresses_from_write_to_read` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_partial_reads_preserve_the_unread_loop_suffix` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_delimited_read_then_drain_completes_a_framed_workflow` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_reset_discards_one_frame_before_a_new_frame` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_zero_timeout_reads_available_data_without_waiting` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_close_reopen_preserves_public_url_configuration` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_loop_control_configuration_projects_status_lines` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_loop_control_line_changes_are_visible_through_public_properties` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_settings_apply_before_open_then_support_loop_io` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_loop_accepts_a_bytearray_and_returns_bytes` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_read_all_and_reset_keep_buffer_state_explicit` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_metadata_and_legacy_tuple_projection_agree` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_metadata_updates_drive_both_usb_public_projections` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_synthetic_metadata_records_sort_and_deduplicate_by_device` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_configuration_constants_and_url_stream_work_together` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_valid_loop_url_remains_selectable_after_invalid_url_attempt` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_deferred_open_applies_all_settings_before_first_loop_frame` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_multiple_delimiters_and_partial_reads_preserve_frame_boundaries` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_control_line_state_survives_configuration_and_loop_transfer` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_metadata_sorting_keeps_usb_projection_fields_attached_to_each_device` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_settings_round_trip_and_buffer_reset_are_independent_public_steps` | integration | Cross-View Invariants | covered |

final_scoreable: 61
