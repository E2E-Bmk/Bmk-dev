# Spec Test Map

task_id: pgqueuer-fullrepro-001
spec_version: v2
oracle_version: 2026-07-10-specv2-scheduler
oracle_source: generated_only
reference_gate: WSL reference_score.json passed 59/59 expanded cases on Linux for spec_v2 scheduler mapping refresh
scorer_isolation: --remove-path pgqueuer

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| filter/generated_tests.py::test_top_level_public_imports_available | generated | atomic | Installable Surface | covered | behavioral generated oracle |
| filter/generated_tests.py::test_in_memory_factory_wires_public_managers_and_queries | generated | integration | Public API | covered | behavioral generated oracle |
| filter/generated_tests.py::test_install_upgrade_and_schema_checks_are_noops | generated | atomic | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_enqueue_single_returns_monotonic_job_id_and_log | generated | atomic | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_enqueue_batch_preserves_order_and_payloads | generated | system_e2e | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_raises_for_zero_batch_size | generated | integration | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_empty_entrypoints_returns_empty | generated | integration | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_filters_by_registered_entrypoints | generated | system_e2e | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_orders_by_priority_then_id | generated | system_e2e | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_marks_jobs_picked_and_job_status_reflects_latest | generated | system_e2e | Product State Model | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_respects_per_entrypoint_concurrency_limit | generated | system_e2e | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dequeue_respects_global_concurrency_limit | generated | system_e2e | Queue Processing Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_deferred_job_is_hidden_until_eligible | generated | atomic | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_next_deferred_eta_none_when_no_matching_deferred_work | generated | atomic | Queue And Enqueue Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_decorator_registers_and_returns_function | generated | atomic | Public API | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_duplicate_name_raises_runtime_error | generated | atomic | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_rejects_non_integer_concurrency_limit | generated | atomic | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_rejects_negative_concurrency_limit | generated | atomic | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_rejects_non_boolean_accepts_context | generated | integration | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_entrypoint_rejects_unknown_failure_policy | generated | atomic | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_queue_manager_run_drain_processes_priority_order_and_success_logs | generated | system_e2e | Queue Processing Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_context_auto_detects_context_annotation | generated | integration | Queue Processing Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_accepts_context_false_suppresses_annotation_injection | generated | integration | Queue Processing Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_run_rejects_too_low_max_concurrent_tasks | generated | atomic | Error Semantics | covered | behavioral generated oracle |
| filter/generated_tests.py::test_retry_requested_defaults_and_reason_attributes | generated | atomic | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_retry_requested_requeues_same_job_and_increments_attempts | generated | system_e2e | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_retry_preserves_payload_priority_and_job_id | generated | atomic | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_unhandled_exception_delete_policy_logs_exception_and_removes_job | generated | system_e2e | Cross-View Invariants | covered | behavioral generated oracle |
| filter/generated_tests.py::test_unhandled_exception_hold_policy_keeps_failed_job_visible | generated | system_e2e | Cross-View Invariants | covered | behavioral generated oracle |
| filter/generated_tests.py::test_requeue_jobs_restores_failed_job_and_resets_attempts | generated | system_e2e | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_requeue_jobs_ignores_non_failed_and_missing_ids | generated | atomic | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_mark_job_as_cancelled_removes_active_job_and_logs_status | generated | atomic | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_mark_job_as_cancelled_ignores_missing_ids | generated | atomic | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_clear_queue_without_filter_removes_jobs_without_delete_logs | generated | integration | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_clear_queue_with_entrypoint_logs_deleted_for_matching_jobs | generated | integration | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_clear_queue_with_entrypoint_list_filters_any_match | generated | integration | Retry, Failure, And Cancellation Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dedupe_key_rejects_duplicate_active_job | generated | atomic | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dedupe_key_released_after_successful_log | generated | system_e2e | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_dedupe_key_released_after_failed_hold | generated | integration | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_queue_size_groups_by_entrypoint_priority_and_status | generated | atomic | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_queue_size_counts_active_jobs_by_entrypoint | generated | atomic | Dedupe, Logs, Statistics, And Schema Behavior | covered | filterfix-v3 uses specified queue_size projection for active queue counts |
| filter/generated_tests.py::test_queue_log_is_append_ordered_across_transitions | generated | system_e2e | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_log_statistics_aggregates_once_and_respects_limit | generated | integration | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_clear_statistics_log_removes_selected_entrypoint_only | generated | integration | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_clear_queue_log_removes_selected_entrypoint_only | generated | integration | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_uninstall_clears_jobs_logs_statistics_schedules_and_dedupe | generated | atomic | Dedupe, Logs, Statistics, And Schema Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_schedule_decorator_registers_and_returns_function | generated | atomic | Public API | covered | behavioral generated oracle |
| filter/generated_tests.py::test_schedule_invalid_cron_raises_value_error | generated | atomic | Scheduling Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_schedule_duplicate_normalized_pair_raises_runtime_error | generated | atomic | Scheduling Behavior | covered | behavioral generated oracle |
| filter/generated_tests.py::test_schedule_six_field_trailing_seconds_is_registered | generated | atomic | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive the due Schedule first; this row also covers six-field cron registration and queued schedule storage |
| filter/generated_tests.py::test_scheduler_run_populates_peek_schedule_with_registered_schedule | generated | integration | Scheduling Behavior | covered | spec_v2 states scheduler dispatch calls the handler with the due Schedule and queued storage remains visible through peek_schedule |
| filter/generated_tests.py::test_scheduler_run_skips_duplicate_entrypoint_expression | generated | integration | Scheduling Behavior | covered | spec_v2 states scheduler dispatch calls the handler with the due Schedule; duplicate insert behavior remains covered by Scheduling Behavior |
| filter/generated_tests.py::test_scheduler_run_marks_due_schedule_picked_and_restores_queued | generated | system_e2e | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive the due Schedule first and set_schedule_queued returns the schedule to queued with last_run |
| filter/generated_tests.py::test_delete_schedule_by_entrypoint_removes_matching_schedules | generated | integration | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive the due Schedule first; deletion is verified through the public schedule projection |
| filter/generated_tests.py::test_clear_schedule_removes_all_schedules | generated | integration | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive the due Schedule first; clear_schedule is verified through the public schedule projection |
| filter/generated_tests.py::test_schedule_dispatch_injects_schedule_context_resources_and_requeues | generated | system_e2e | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive Schedule first and ScheduleContext second when context injection applies |
| filter/generated_tests.py::test_update_schedule_heartbeat_changes_heartbeat_without_status_change | generated | atomic | Scheduling Behavior | covered | spec_v2 states scheduled handlers receive the due Schedule first; heartbeat mutation is verified through the public schedule projection |

Total: 57 | kept (covered): 57 | spec_gap: 0 | source-only: 0 | excluded: 327 | final scoreable: 57
