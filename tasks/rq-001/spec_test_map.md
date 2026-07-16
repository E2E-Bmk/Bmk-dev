# rq-001 Spec Test Map

oracle_version: 2026-07-16-stage3-generated
oracle_source: generated_only
reference_observation: generated tests were written from executed reference behavior using the local reference package and fakeredis; source files were not read for assertion construction.
track_a: no upstream tests retained after public-carrier rewrite audit

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| oracle/test_atomic.py::test_top_level_installable_surface_exports_core_names | generated | atomic | Installable Surface | covered | top-level public exports named in the spec |
| oracle/test_atomic.py::test_documented_public_modules_export_scoped_classes | generated | atomic | Installable Surface | covered | documented module exports named in the spec |
| oracle/test_atomic.py::test_queue_requires_connection | generated | atomic | Error Semantics | covered | Queue constructor failure condition |
| oracle/test_atomic.py::test_queue_default_name_and_empty_count | generated | atomic | Queueing and Job Creation | covered | Queue default name and empty queue views |
| oracle/test_integration.py::test_queue_all_lists_known_queue_after_enqueue | generated | integration | Product State Model | covered | queue persisted state is visible through Queue.all |
| oracle/test_integration.py::test_enqueue_persists_job_status_origin_and_arguments | generated | integration | Queueing and Job Creation | covered | enqueue persists job options and callable arguments |
| oracle/test_integration.py::test_enqueue_at_front_changes_ready_order | generated | integration | Cross-View Invariants | covered | at_front ordering in queue API |
| oracle/test_atomic.py::test_get_jobs_matches_job_ids_order | generated | atomic | Cross-View Invariants | covered | job id and job object ready-queue views align |
| oracle/test_atomic.py::test_queue_remove_removes_one_ready_job | generated | atomic | Public API | covered | Queue.remove removes a queued job id |
| oracle/test_atomic.py::test_get_job_ids_supports_offset_and_length_window | generated | atomic | Public API | covered | Queue.get_job_ids offset and length view |
| oracle/test_atomic.py::test_job_requires_connection | generated | atomic | Error Semantics | covered | Job constructor failure condition |
| oracle/test_atomic.py::test_job_create_rejects_non_string_id | generated | atomic | Error Semantics | covered | custom job id type validation |
| oracle/test_atomic.py::test_job_create_rejects_id_with_invalid_characters | generated | atomic | Error Semantics | covered | custom job id character validation |
| oracle/test_atomic.py::test_job_exists_tracks_persisted_job | generated | atomic | Public API | covered | Job.exists tracks persisted jobs |
| oracle/test_atomic.py::test_job_fetch_missing_raises_named_error | generated | atomic | Error Semantics | covered | missing Job.fetch error type name |
| oracle/test_atomic.py::test_job_fetch_many_preserves_requested_order_and_missing_slots | generated | atomic | Public API | covered | Job.fetch_many aligns with requested ids |
| oracle/test_atomic.py::test_job_metadata_round_trips_through_save_meta_and_get_meta | generated | atomic | Public API | covered | Job metadata save/get behavior |
| oracle/test_atomic.py::test_return_value_is_none_before_successful_execution | generated | atomic | Job Lifecycle and Results | covered | return value absent before a successful result |
| oracle/test_atomic.py::test_dependency_empty_list_is_rejected | generated | atomic | Error Semantics | covered | Dependency rejects empty lists |
| oracle/test_atomic.py::test_dependency_rejects_unsupported_values | generated | atomic | Error Semantics | covered | Dependency rejects unsupported values |
| oracle/test_atomic.py::test_repeat_rejects_non_positive_times | generated | atomic | Scheduling, Repeating, Retries, and Rate Limits | covered | Repeat validation for times |
| oracle/test_atomic.py::test_repeat_keeps_times_and_interval_configuration | generated | atomic | Scheduling, Repeating, Retries, and Rate Limits | covered | Repeat public configuration fields |
| oracle/test_atomic.py::test_retry_keeps_max_interval_and_front_configuration | generated | atomic | Scheduling, Repeating, Retries, and Rate Limits | covered | Retry public configuration fields |
| oracle/test_atomic.py::test_json_serializer_round_trips_json_compatible_values | generated | atomic | Installable Surface | covered | JSONSerializer accepted public serializer |
| oracle/test_atomic.py::test_group_fetch_missing_group_raises_named_error | generated | atomic | Error Semantics | covered | missing group error type name |
| oracle/test_integration.py::test_successful_simple_worker_execution_records_finished_result | generated | integration | Cross-View Invariants | covered | successful worker execution updates job, result, and registry views |
| oracle/test_integration.py::test_failed_simple_worker_execution_records_failed_registry_and_exception_info | generated | integration | Cross-View Invariants | covered | failed worker execution updates job, result, and registry views |
| oracle/test_integration.py::test_finished_job_return_value_survives_refetch | generated | integration | Job Lifecycle and Results | covered | finished result visible after Job.fetch |
| oracle/test_integration.py::test_failed_registry_requeue_moves_job_back_to_ready_queue | generated | integration | Registries, Groups, and Monitoring Views | covered | FailedJobRegistry.requeue queue/registry transition |
| oracle/test_integration.py::test_job_requeue_returns_failed_job_to_origin_queue | generated | integration | Dependencies, Cancellation, and Requeueing | covered | Job.requeue queue transition |
| oracle/test_integration.py::test_requeue_job_helper_returns_failed_job_to_queue | generated | integration | Dependencies, Cancellation, and Requeueing | covered | requeue_job helper transition |
| oracle/test_integration.py::test_cancel_queued_job_moves_to_canceled_registry | generated | integration | Registries, Groups, and Monitoring Views | covered | Job.cancel moves queued job to canceled registry |
| oracle/test_integration.py::test_cancel_job_helper_cancels_by_id | generated | integration | Dependencies, Cancellation, and Requeueing | covered | cancel_job helper mirrors Job.cancel |
| oracle/test_integration.py::test_delete_job_removes_queue_and_registry_membership | generated | integration | Dependencies, Cancellation, and Requeueing | covered | Job.delete removes record and registry membership |
| oracle/test_integration.py::test_enqueue_in_creates_scheduled_job_not_ready_job | generated | integration | Scheduling, Repeating, Retries, and Rate Limits | covered | enqueue_in creates scheduled non-ready job |
| oracle/test_integration.py::test_enqueue_at_records_scheduled_time | generated | integration | Scheduling, Repeating, Retries, and Rate Limits | covered | enqueue_at scheduled-time registry view |
| oracle/test_integration.py::test_sync_queue_executes_success_immediately | generated | integration | Representative Workflows | covered | synchronous producer workflow success path |
| oracle/test_integration.py::test_sync_queue_records_failed_state_on_exception | generated | integration | Representative Workflows | covered | synchronous producer workflow failure path |
| oracle/test_integration.py::test_dependency_places_dependent_job_in_deferred_registry | generated | integration | Dependencies, Cancellation, and Requeueing | covered | dependent job deferred state and registry |
| oracle/test_integration.py::test_finished_dependency_enqueues_dependent_after_worker_run | generated | system_e2e | Representative Workflows | covered | worker workflow completes dependency and dependent job |
| oracle/test_integration.py::test_dependency_allow_failure_enqueues_dependent_after_failed_parent | generated | system_e2e | Dependencies, Cancellation, and Requeueing | covered | allow_failure dependency workflow |
| oracle/test_integration.py::test_enqueue_many_with_prepared_data_returns_jobs_in_order | generated | integration | Queueing and Job Creation | covered | prepare_data/enqueue_many batch creation |
| oracle/test_integration.py::test_group_enqueue_many_attaches_jobs_to_group | generated | integration | Registries, Groups, and Monitoring Views | covered | Group.enqueue_many and group job view |
| oracle/test_integration.py::test_get_current_job_inside_execution_returns_running_job_id | generated | integration | Product State Model | covered | get_current_job inside executing job |
| oracle/test_integration.py::test_worker_default_queue_priority_processes_first_non_empty_queue | generated | system_e2e | Workers and Worker Commands | covered | default worker queue priority with max_jobs |
| oracle/test_integration.py::test_worker_burst_processes_all_available_jobs_and_returns_true | generated | system_e2e | Workers and Worker Commands | covered | burst worker processes available jobs |
| oracle/test_integration.py::test_worker_all_and_count_are_empty_after_graceful_burst_exit | generated | integration | Product State Model | covered | worker registration is removed after graceful burst exit |
| oracle/test_integration.py::test_worker_max_jobs_limits_burst_processing | generated | system_e2e | Workers and Worker Commands | covered | max_jobs limits burst processing |
| oracle/test_integration.py::test_result_history_records_newest_result_for_success | generated | integration | Job Lifecycle and Results | covered | job.results records successful result history |
| oracle/test_integration.py::test_exception_retry_with_zero_interval_requeues_then_fails_terminally | generated | integration | Scheduling, Repeating, Retries, and Rate Limits | covered | exception retry terminal result after max attempts |
| oracle/test_integration.py::test_return_based_retry_records_retried_result | generated | integration | Scheduling, Repeating, Retries, and Rate Limits | covered | return-based Retry terminal behavior |
| oracle/test_integration.py::test_json_serializer_queue_and_worker_preserve_arguments_and_result | generated | integration | Cross-View Invariants | covered | producer and worker use JSON serializer consistently |
| oracle/test_atomic.py::test_send_stop_job_command_rejects_non_executing_job_id | generated | atomic | Error Semantics | covered | send_stop_job_command invalid target error |
| oracle/test_integration.py::test_cli_help_exits_zero_and_lists_core_commands | generated | system_e2e | CLI Behavior | covered | top-level CLI help lists commands and exits zero |
| oracle/test_integration.py::test_cli_invalid_command_exits_nonzero | generated | system_e2e | CLI Behavior | covered | invalid CLI command exits with usage error |
| oracle/test_integration.py::test_cli_worker_help_exits_zero | generated | system_e2e | CLI Behavior | covered | worker subcommand help exits zero |

Total: 56 | kept (covered): 56 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 56
Layer counts: atomic=23 | integration=25 | system_e2e=8 | integration+system_e2e=33
Section counts: CLI Behavior=3; Cross-View Invariants=5; Dependencies, Cancellation, and Requeueing=6; Error Semantics=9; Installable Surface=3; Job Lifecycle and Results=3; Product State Model=3; Public API=5; Queueing and Job Creation=3; Registries, Groups, and Monitoring Views=3; Representative Workflows=3; Scheduling, Repeating, Retries, and Rate Limits=7; Workers and Worker Commands=3
