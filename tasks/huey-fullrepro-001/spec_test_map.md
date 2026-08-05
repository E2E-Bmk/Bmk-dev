# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_immediate_memory_huey_uses_memory_storage` | atomic | Storage And Introspection | covered |
| 2 | `oracle/test_atomic.py::test_huey_immediate_property_can_toggle_execution_mode` | atomic | Tasks And Execution | covered |
| 3 | `oracle/test_atomic.py::test_empty_huey_exposes_zero_queue_schedule_and_result_counts` | atomic | Storage And Introspection | covered |
| 4 | `oracle/test_atomic.py::test_task_wrapper_call_local_returns_function_value` | atomic | Tasks And Execution | covered |
| 5 | `oracle/test_atomic.py::test_task_wrapper_s_exposes_task_arguments_and_keywords` | atomic | Tasks And Execution | covered |
| 6 | `oracle/test_atomic.py::test_task_wrapper_schedule_requires_eta_or_delay` | atomic | Scheduling And Periodic Tasks | covered |
| 7 | `oracle/test_atomic.py::test_immediate_task_call_returns_ready_result` | atomic | Tasks And Execution | covered |
| 8 | `oracle/test_atomic.py::test_result_preserve_and_reset_control_result_consumption` | atomic | Results | covered |
| 9 | `oracle/test_atomic.py::test_task_then_returns_original_task_and_adds_completion` | atomic | Pipelines And Groups | covered |
| 10 | `oracle/test_atomic.py::test_task_error_returns_original_task_and_adds_error_handler` | atomic | Pipelines And Groups | covered |
| 11 | `oracle/test_atomic.py::test_crontab_wildcard_matches_fixed_timestamp` | atomic | Scheduling And Periodic Tasks | covered |
| 12 | `oracle/test_atomic.py::test_crontab_interval_matches_only_selected_minutes` | atomic | Scheduling And Periodic Tasks | covered |
| 13 | `oracle/test_atomic.py::test_crontab_range_and_list_match_selected_hours` | atomic | Scheduling And Periodic Tasks | covered |
| 14 | `oracle/test_atomic.py::test_crontab_strict_rejects_unsupported_input` | atomic | Scheduling And Periodic Tasks | covered |
| 15 | `oracle/test_atomic.py::test_crontab_daily_and_hourly_shortcuts_match_expected_times` | atomic | Scheduling And Periodic Tasks | covered |
| 16 | `oracle/test_atomic.py::test_serializer_round_trips_nested_python_values` | atomic | Serialization And Signing | covered |
| 17 | `oracle/test_atomic.py::test_serializer_gzip_round_trip_preserves_bytes` | atomic | Serialization And Signing | covered |
| 18 | `oracle/test_atomic.py::test_serializer_zlib_round_trip_preserves_mapping` | atomic | Serialization And Signing | covered |
| 19 | `oracle/test_atomic.py::test_signed_serializer_round_trips_payload` | atomic | Serialization And Signing | covered |
| 20 | `oracle/test_atomic.py::test_signed_serializer_rejects_tampered_payload` | atomic | Serialization And Signing | covered |
| 21 | `oracle/test_atomic.py::test_constant_time_compare_reports_equal_and_unequal_bytes` | atomic | Serialization And Signing | covered |
| 22 | `oracle/test_atomic.py::test_memory_storage_empty_dequeue_returns_none` | atomic | Storage And Introspection | covered |
| 23 | `oracle/test_atomic.py::test_memory_storage_enqueued_items_preserve_fifo_order` | atomic | Storage And Introspection | covered |
| 24 | `oracle/test_atomic.py::test_memory_storage_prioritizes_higher_priority_items` | atomic | Storage And Introspection | covered |
| 25 | `oracle/test_atomic.py::test_memory_storage_reads_only_schedule_items_due_by_timestamp` | atomic | Storage And Introspection | covered |
| 26 | `oracle/test_atomic.py::test_memory_storage_peek_and_pop_data_have_distinct_lifecycles` | atomic | Storage And Introspection | covered |
| 27 | `oracle/test_atomic.py::test_memory_storage_put_if_empty_is_idempotent` | atomic | Storage And Introspection | covered |
| 28 | `oracle/test_atomic.py::test_memory_storage_counter_increment_and_delete_are_publicly_observable` | atomic | Storage And Introspection | covered |
| 29 | `oracle/test_atomic.py::test_memory_storage_result_items_and_flush_results` | atomic | Storage And Introspection | covered |
| 30 | `oracle/test_atomic.py::test_memory_storage_flush_queue_and_schedule_clear_both_views` | atomic | Storage And Introspection | covered |
| 31 | `oracle/test_atomic.py::test_error_named_tuple_exposes_metadata` | atomic | Results | covered |
| 32 | `oracle/test_atomic.py::test_cancel_execution_preserves_retry_option` | atomic | Execution Controls | covered |
| 33 | `oracle/test_atomic.py::test_retry_task_preserves_eta_and_delay_options` | atomic | Execution Controls | covered |
| 34 | `oracle/test_atomic.py::test_rate_limit_usage_can_be_read_and_reset` | atomic | Rate Limiting | covered |
| 35 | `oracle/test_atomic.py::test_task_lock_acquire_reports_state_and_release_clears_it` | atomic | Execution Controls | covered |
| 36 | `oracle/test_atomic.py::test_huey_put_get_and_delete_expose_serialized_data` | atomic | Storage And Introspection | covered |
| 37 | `oracle/test_atomic.py::test_memory_huey_results_false_omits_result_handle` | atomic | Results | covered |
| 38 | `oracle/test_atomic.py::test_memory_huey_store_none_preserves_none_result` | atomic | Results | covered |
| 39 | `oracle/test_integration.py::test_enqueue_dequeue_execute_and_result_get_share_task_state` | integration | Tasks And Execution | covered |
| 40 | `oracle/test_integration.py::test_serialized_task_round_trip_preserves_public_task_data` | integration | Tasks And Execution | covered |
| 41 | `oracle/test_integration.py::test_pending_returns_deserialized_tasks_and_honors_limit` | integration | Tasks And Execution | covered |
| 42 | `oracle/test_integration.py::test_tuple_pipeline_passes_returned_tuple_as_next_arguments` | integration | Pipelines And Groups | covered |
| 43 | `oracle/test_integration.py::test_dict_pipeline_passes_returned_mapping_as_next_keywords` | integration | Pipelines And Groups | covered |
| 44 | `oracle/test_integration.py::test_task_map_returns_result_group_in_input_order` | integration | Pipelines And Groups | covered |
| 45 | `oracle/test_integration.py::test_group_enqueues_distinct_tasks_and_collects_results` | integration | Pipelines And Groups | covered |
| 46 | `oracle/test_integration.py::test_chord_collects_member_results_before_callback` | integration | Pipelines And Groups | covered |
| 47 | `oracle/test_integration.py::test_chord_pipeline_exposes_callback_pipeline_results` | integration | Pipelines And Groups | covered |
| 48 | `oracle/test_integration.py::test_failed_task_surfaces_public_task_exception` | integration | Results | covered |
| 49 | `oracle/test_integration.py::test_retrying_task_requeues_then_stores_success` | integration | Execution Controls | covered |
| 50 | `oracle/test_integration.py::test_pre_and_post_execute_hooks_observe_task_lifecycle` | integration | Signals And Hooks | covered |
| 51 | `oracle/test_integration.py::test_signal_handler_receives_enqueue_execute_and_complete` | integration | Signals And Hooks | covered |
| 52 | `oracle/test_integration.py::test_disconnect_signal_stops_selected_signal_delivery` | integration | Signals And Hooks | covered |
| 53 | `oracle/test_integration.py::test_task_class_revoke_and_restore_control_execution` | integration | Execution Controls | covered |
| 54 | `oracle/test_integration.py::test_revoke_once_blocks_one_task_instance_then_restores` | integration | Execution Controls | covered |
| 55 | `oracle/test_integration.py::test_result_revoke_restore_can_restore_queued_task` | integration | Execution Controls | covered |
| 56 | `oracle/test_integration.py::test_scheduled_task_moves_from_schedule_to_execution` | integration | Scheduling And Periodic Tasks | covered |
| 57 | `oracle/test_integration.py::test_scheduled_items_and_flush_remove_scheduled_tasks` | integration | Scheduling And Periodic Tasks | covered |
| 58 | `oracle/test_integration.py::test_expired_task_emits_no_result_and_public_expired_signal` | integration | Signals And Hooks | covered |
| 59 | `oracle/test_integration.py::test_task_priorities_control_dequeue_execution_order` | integration | Execution Controls | covered |
| 60 | `oracle/test_integration.py::test_switching_immediate_mode_changes_enqueue_execution` | integration | Tasks And Execution | covered |
| 61 | `oracle/test_integration.py::test_lock_decorator_and_lock_signal_integrate_with_task_execution` | integration | Signals And Hooks | covered |
| 62 | `oracle/test_integration.py::test_rate_limit_decorator_emits_rate_limit_error_without_retry` | integration | Rate Limiting | covered |
| 63 | `oracle/test_integration.py::test_context_task_receives_public_task_object` | integration | Tasks And Execution | covered |
| 64 | `oracle/test_integration.py::test_periodic_task_registration_and_execution_use_crontab` | integration | Scheduling And Periodic Tasks | covered |
| 65 | `oracle/test_integration.py::test_compressed_huey_serializer_preserves_task_result` | integration | Serialization And Signing | covered |
| 66 | `oracle/test_integration.py::test_huey_result_lookup_reads_result_by_task_id` | integration | Results | covered |
| 67 | `oracle/test_integration.py::test_all_results_exposes_completed_task_ids_before_consumption` | integration | Results | covered |
| 68 | `oracle/test_integration.py::test_huey_flush_clears_queue_schedule_results_and_locks` | integration | Storage And Introspection | covered |
| 69 | `oracle/test_integration.py::test_result_group_iteration_and_indexing_resolve_member_results` | integration | Pipelines And Groups | covered |
| 70 | `oracle/test_integration.py::test_result_reschedule_revokes_original_and_creates_new_task` | integration | Scheduling And Periodic Tasks | covered |
| 71 | `oracle/test_integration.py::test_error_signal_and_error_result_are_consistent` | integration | Signals And Hooks | covered |
| 72 | `oracle/test_integration.py::test_revoked_task_emits_public_revoked_signal` | integration | Signals And Hooks | covered |
| 73 | `oracle/test_integration.py::test_call_local_and_queued_execution_produce_same_value` | integration | Tasks And Execution | covered |

final_scoreable: 73
