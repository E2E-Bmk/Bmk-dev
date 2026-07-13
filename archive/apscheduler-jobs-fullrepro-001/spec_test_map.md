# APScheduler spec test map

oracle_version: 2026-07-04T141500Z
filter/oracle_source: generated_only
source_file: filter/oracle_repo/tests/test_generated_core.py

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| tests/test_generated_core.py::test_default_sync_scheduler_components_and_state | generated | atomic | ## Public API | covered | default sync scheduler components and state |
| tests/test_generated_core.py::test_sync_scheduler_context_variable_is_set_inside_context | generated | integration | ## Job Executors And Context Variables | covered | sync scheduler context variable is set inside context |
| tests/test_generated_core.py::test_configure_task_creates_task_and_task_added_event | generated | integration | ## Task Configuration | covered | configure task creates task and task added event |
| tests/test_generated_core.py::test_configure_task_updates_existing_task_and_emits_update | generated | integration | ## Task Configuration | covered | configure task updates existing task and emits update |
| tests/test_generated_core.py::test_configure_task_merges_defaults_decorator_and_direct_metadata | generated | atomic | ## Task Configuration | covered | configure task merges defaults decorator and direct metadata |
| tests/test_generated_core.py::test_task_decorator_rejects_non_callable | generated | atomic | ## Task Configuration | covered | task decorator rejects non callable |
| tests/test_generated_core.py::test_task_decorator_rejects_double_decoration | generated | atomic | ## Task Configuration | covered | task decorator rejects double decoration |
| tests/test_generated_core.py::test_configure_task_rejects_invalid_identifier_type | generated | atomic | ## Error Semantics | covered | configure task rejects invalid identifier type |
| tests/test_generated_core.py::test_get_tasks_returns_sorted_by_id | generated | atomic | ## Memory Data Store | covered | get tasks returns sorted by id |
| tests/test_generated_core.py::test_add_schedule_returns_supplied_id_and_stores_schedule | generated | integration | ## Schedule Lifecycle | covered | add schedule returns supplied id and stores schedule |
| tests/test_generated_core.py::test_add_schedule_without_id_generates_string_identifier | generated | atomic | ## Schedule Lifecycle | covered | add schedule without id generates string identifier |
| tests/test_generated_core.py::test_schedule_added_event_contains_schedule_and_task_identity | generated | integration | ## Schedule Lifecycle | covered | schedule added event contains schedule and task identity |
| tests/test_generated_core.py::test_schedule_get_missing_raises_schedule_lookup_error | generated | atomic | ## Error Semantics | covered | schedule get missing raises schedule lookup error |
| tests/test_generated_core.py::test_remove_schedule_removes_view_and_emits_event | generated | integration | ## Schedule Lifecycle | covered | remove schedule removes view and emits event |
| tests/test_generated_core.py::test_remove_missing_schedule_is_noop | generated | atomic | ## Schedule Lifecycle | covered | remove missing schedule is noop |
| tests/test_generated_core.py::test_pause_and_unpause_schedule_change_public_state_and_events | generated | integration | ## Schedule Lifecycle | covered | pause and unpause schedule change public state and events |
| tests/test_generated_core.py::test_unpause_resume_from_advances_interval_schedule | generated | integration | ## Schedule Lifecycle | covered | unpause resume from advances interval schedule |
| tests/test_generated_core.py::test_conflict_policy_do_nothing_preserves_existing_schedule | generated | atomic | ## Schedule Lifecycle | covered | conflict policy do nothing preserves existing schedule |
| tests/test_generated_core.py::test_conflict_policy_replace_updates_schedule | generated | atomic | ## Schedule Lifecycle | covered | conflict policy replace updates schedule |
| tests/test_generated_core.py::test_conflict_policy_exception_raises_conflicting_id_error | generated | atomic | ## Error Semantics | covered | conflict policy exception raises conflicting id error |
| tests/test_generated_core.py::test_paused_due_schedule_does_not_create_job_until_unpaused | generated | system_e2e | ## Cross-View Invariants | covered | paused due schedule does not create job until unpaused |
| tests/test_generated_core.py::test_scheduler_role_scheduler_processes_schedule_without_running_job | generated | system_e2e | ## Scheduler Lifecycle | covered | scheduler role scheduler processes schedule without running job |
| tests/test_generated_core.py::test_scheduler_role_worker_runs_existing_direct_job | generated | system_e2e | ## Scheduler Lifecycle | covered | scheduler role worker runs existing direct job |
| tests/test_generated_core.py::test_add_job_returns_uuid_and_job_is_visible_before_processing | generated | atomic | ## Job Lifecycle | covered | add job returns uuid and job is visible before processing |
| tests/test_generated_core.py::test_add_job_publishes_job_added_event | generated | integration | ## Job Lifecycle | covered | add job publishes job added event |
| tests/test_generated_core.py::test_get_job_result_wait_false_before_run_raises_lookup_error | generated | atomic | ## Error Semantics | covered | get job result wait false before run raises lookup error |
| tests/test_generated_core.py::test_run_job_returns_callable_value | generated | system_e2e | ## Job Lifecycle | covered | run job returns callable value |
| tests/test_generated_core.py::test_run_job_reraises_callable_exception | generated | system_e2e | ## Error Semantics | covered | run job reraises callable exception |
| tests/test_generated_core.py::test_successful_job_result_is_consumed_after_retrieval | generated | integration | ## Job Lifecycle | covered | successful job result is consumed after retrieval |
| tests/test_generated_core.py::test_job_events_are_emitted_in_lifecycle_order | generated | system_e2e | ## Cross-View Invariants | covered | job events are emitted in lifecycle order |
| tests/test_generated_core.py::test_current_job_context_variable_identifies_running_job | generated | integration | ## Job Executors And Context Variables | covered | current job context variable identifies running job |
| tests/test_generated_core.py::test_current_scheduler_context_variable_visible_to_sync_job | generated | integration | ## Job Executors And Context Variables | covered | current scheduler context variable visible to sync job |
| tests/test_generated_core.py::test_threadpool_executor_runs_sync_job_off_calling_thread | generated | integration | ## Job Executors And Context Variables | covered | threadpool executor runs sync job off calling thread |
| tests/test_generated_core.py::test_async_scheduler_async_executor_runs_on_event_loop | generated | integration | ## Job Executors And Context Variables | covered | async scheduler async executor runs on event loop |
| tests/test_generated_core.py::test_async_scheduler_context_variable_visible_to_async_job | generated | integration | ## Job Executors And Context Variables | covered | async scheduler context variable visible to async job |
| tests/test_generated_core.py::test_scheduler_start_and_stop_publish_lifecycle_events | generated | system_e2e | ## Scheduler Lifecycle | covered | scheduler start and stop publish lifecycle events |
| tests/test_generated_core.py::test_wait_until_stopped_returns_after_stop_job | generated | system_e2e | ## Scheduler Lifecycle | covered | wait until stopped returns after stop job |
| tests/test_generated_core.py::test_finished_schedule_removed_by_cleanup | generated | system_e2e | ## Scheduler Lifecycle | covered | finished schedule removed by cleanup |
| tests/test_generated_core.py::test_job_result_expiration_cleanup_removes_result | generated | system_e2e | ## Memory Data Store | covered | job result expiration cleanup removes result |
| tests/test_generated_core.py::test_date_trigger_fires_once_then_exhausts | generated | atomic | ## Triggers | covered | date trigger fires once then exhausts |
| tests/test_generated_core.py::test_date_trigger_state_round_trip_preserves_completion | generated | atomic | ## Triggers | covered | date trigger state round trip preserves completion |
| tests/test_generated_core.py::test_interval_trigger_rejects_zero_interval | generated | atomic | ## Error Semantics | covered | interval trigger rejects zero interval |
| tests/test_generated_core.py::test_interval_trigger_rejects_end_before_start | generated | atomic | ## Error Semantics | covered | interval trigger rejects end before start |
| tests/test_generated_core.py::test_interval_trigger_returns_start_then_interval_steps_until_end | generated | atomic | ## Triggers | covered | interval trigger returns start then interval steps until end |
| tests/test_generated_core.py::test_interval_trigger_state_round_trip_continues_from_last_fire_time | generated | atomic | ## Triggers | covered | interval trigger state round trip continues from last fire time |
| tests/test_generated_core.py::test_memory_datastore_get_next_schedule_run_time_tracks_earliest | generated | integration | ## Memory Data Store | covered | memory datastore get next schedule run time tracks earliest |
| tests/test_generated_core.py::test_memory_datastore_task_lookup_error_for_missing_task | generated | atomic | ## Error Semantics | covered | memory datastore task lookup error for missing task |
| tests/test_generated_core.py::test_job_result_from_job_sets_expiration_from_finish_time | generated | atomic | ## Public API | covered | job result from job sets expiration from finish time |
| tests/test_generated_core.py::test_job_original_scheduled_time_subtracts_jitter | generated | integration | ## Public API | covered | job original scheduled time subtracts jitter |
| tests/test_generated_core.py::test_job_result_not_ready_exception_is_public_constructible | generated | atomic | ## Error Semantics | covered | job result not ready exception is public constructible |
| tests/test_generated_core.py::test_local_event_broker_delivers_one_shot_only_once | generated | integration | ## Events | covered | local event broker delivers one shot only once |
| tests/test_generated_core.py::test_local_event_broker_filters_event_types | generated | integration | ## Events | covered | local event broker filters event types |
| tests/test_generated_core.py::test_get_next_event_returns_matching_event | generated | integration | ## Events | covered | get next event returns matching event |
| tests/test_generated_core.py::test_schedule_metadata_inherits_task_metadata_and_overrides_top_level | generated | integration | ## Cross-View Invariants | covered | schedule metadata inherits task metadata and overrides top level |
| tests/test_generated_core.py::test_direct_job_metadata_inherits_task_metadata_and_overrides_top_level | generated | integration | ## Cross-View Invariants | covered | direct job metadata inherits task metadata and overrides top level |
| tests/test_generated_core.py::test_max_running_jobs_limits_second_acquisition_until_release | generated | integration | ## Memory Data Store | covered | max running jobs limits second acquisition until release |
| tests/test_generated_core.py::test_state_model_views_agree_for_task_schedule_and_job | generated | system_e2e | ## Product State Model | covered | state model views agree for task schedule and job |
| tests/test_generated_core.py::test_direct_job_representative_workflow_events_and_result | generated | system_e2e | ## Representative Workflows | covered | direct job representative workflow events and result |
| tests/test_generated_core.py::test_date_schedule_representative_workflow_pause_unpause_remove | generated | system_e2e | ## Representative Workflows | covered | date schedule representative workflow pause unpause remove |
| tests/test_generated_core.py::test_cross_view_schedule_event_matches_stored_schedule | generated | system_e2e | ## Cross-View Invariants | covered | cross view schedule event matches stored schedule |

Total: 60 | kept (covered): 60 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 60
