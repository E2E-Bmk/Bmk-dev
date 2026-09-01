| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_run_returns_coroutine_value | atomic | Installable Surface | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_run_passes_all_arguments_to_coroutine | atomic | Installable Surface | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_run_rejects_nested_runtime | atomic | Installable Surface | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_product_state_task_projection_records_normal_completion | system_e2e | Product State Model | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_product_state_coordination_projection_retains_unfinished_work | system_e2e | Product State Model | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_product_state_universal_projection_shares_result_with_thread | system_e2e | Product State Model | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_task_ids_are_increasing_integers_without_positivity_assumption | atomic | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_task_result_and_exception_raise_before_deterministic_release | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_spawned_task_is_current_task_in_child | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_task_join_returns_child_value | atomic | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_task_wait_leaves_task_terminated | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_task_join_wraps_child_failure_with_cause | atomic | Error Semantics | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_blocking_cancel_terminates_task_and_marks_cancelled | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_spawn_exposes_joined_result | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_next_result_returns_completed_value | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_wait_any_cleans_up_managed_tasks | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_cancel_remaining_terminates_non_daemons | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_adds_ungrouped_task | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_wait_object_uses_non_none_result | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_queue_returns_items_in_fifo_order | atomic | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_priority_queue_returns_lowest_item_first | atomic | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_lifo_queue_returns_latest_item_first | atomic | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_queue_public_size_and_capacity_state | atomic | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_queue_join_waits_for_task_done_obligation | atomic | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_bounded_queue_put_completes_after_consumer_makes_space | integration | Queues | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_event_set_releases_waiter_and_sets_flag | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_result_unwrap_returns_supplied_value | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_result_unwrap_reraises_supplied_exception | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_lock_reports_locked_while_held | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_rlock_allows_recursive_owner_acquisition | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_semaphore_release_makes_waiting_acquisition_eligible | integration | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_condition_wait_requires_held_lock | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_condition_notify_requires_held_lock | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_condition_wait_for_returns_truthy_predicate_value | atomic | Synchronization | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_timeout_after_returns_value_before_deadline | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_timeout_after_raises_task_timeout_when_blocking_operation_expires | atomic | Error Semantics | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_ignore_after_returns_value_before_deadline | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_ignore_after_returns_timeout_result_after_expiry | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_ignore_after_context_reports_non_expiration | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_ignore_after_context_reports_own_expiration | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_atomic.py::test_timeout_context_delivers_task_timeout_to_matching_scope | atomic | Timeouts and Cancellation | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_direct_cancellation_delivers_taskcancelled | integration | Error Semantics | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_nested_outer_timeout_interrupts_inner_with_distinct_error | integration | Error Semantics | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_timeout_escaping_matching_boundary_raises_uncaught_timeout | integration | Error Semantics | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_queue_sync_put_is_visible_to_curio_get | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_queue_curio_put_is_visible_to_sync_get | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_queue_sync_join_observes_task_done | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_queue_without_fd_rejects_fileno | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_event_sync_set_is_visible_to_curio_waiter | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_event_curio_set_is_visible_synchronously | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_event_clear_resets_shared_flag | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_result_sync_value_is_unwrapped_in_curio | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_result_curio_value_is_unwrapped_synchronously | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_result_sync_exception_is_reraised_in_curio | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_universal_result_curio_exception_is_reraised_synchronously | integration | Universal Coordination | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_taskgroup_next_result_reraises_child_failure | integration | Tasks and Task Groups | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_cross_view_task_and_group_project_same_successful_outcome | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_cross_view_universal_event_thread_set_releases_curio_waiter | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_cross_view_universal_result_exception_reaches_asyncio_unchanged | system_e2e | Cross-View Invariants | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_representative_worker_queue_taskgroup_workflow | system_e2e | Representative Workflows | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_representative_event_task_workflow | system_e2e | Representative Workflows | covered | Spec-derived public outcome; no private or exact-message assertion. |
| oracle/test_integration.py::test_representative_universal_result_workflow | system_e2e | Representative Workflows | covered | Spec-derived public outcome; no private or exact-message assertion. |
