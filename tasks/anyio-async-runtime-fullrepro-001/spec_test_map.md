# Spec Test Map - anyio-async-runtime-fullrepro-001

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_upstream_invalid_max_buffer | atomic | Streams and Networking | covered | memory stream rejects invalid buffer size |
| oracle/test_atomic.py::test_upstream_negative_max_buffer | atomic | Streams and Networking | covered | memory stream rejects negative buffer size |
| oracle/test_integration.py::test_upstream_receive_then_send[asyncio] | integration | Streams and Networking | covered | zero-buffer send/receive rendezvous |
| oracle/test_atomic.py::test_upstream_send_nowait_then_receive_nowait[asyncio] | atomic | Streams and Networking | covered | nowait FIFO delivery |
| oracle/test_integration.py::test_upstream_iterate_memory_stream[asyncio] | integration | Streams and Networking | covered | async iteration drains until send close |
| oracle/test_atomic.py::test_upstream_closed_send_stream_errors[asyncio] | atomic | Error Semantics | covered | closed same end and clean EOF exceptions |
| oracle/test_atomic.py::test_upstream_closed_receive_stream_errors[asyncio] | atomic | Error Semantics | covered | closed receive and broken opposite end exceptions |
| oracle/test_integration.py::test_upstream_cancel_receive_restores_nowait_state[asyncio] | integration | Cross-View Invariants | covered | cancelled receive does not consume later send slot |
| oracle/test_integration.py::test_upstream_clone_keeps_other_ends_open[asyncio] | integration | Cross-View Invariants | covered | clone lifecycle projections agree |
| oracle/test_atomic.py::test_upstream_buffered_receive_exactly[asyncio] | atomic | Streams and Networking | covered | buffered exact byte reads |
| oracle/test_atomic.py::test_upstream_buffered_receive_exactly_incomplete[asyncio] | atomic | Error Semantics | covered | IncompleteRead on early EOF |
| oracle/test_atomic.py::test_upstream_buffered_receive_until[asyncio] | atomic | Streams and Networking | covered | delimiter reads return bytes before delimiter |
| oracle/test_atomic.py::test_deprecated_worker_interpreter_alias_warns | atomic | Installable Surface | covered | deprecated top-level spelling warns and aliases public class |
| oracle/test_atomic.py::test_stream_file_public_classes_are_importable | atomic | Installable Surface | covered | public stream file classes and attributes import from documented module |
| oracle/test_atomic.py::test_abc_public_resource_and_task_types_are_importable | atomic | Installable Surface | covered | public ABC resource/task types import from documented module |
| oracle/test_atomic.py::test_available_backend_projection_contains_asyncio | atomic | Public API | covered | available backends are subset of all built-in backends |
| oracle/test_atomic.py::test_all_backends_public_tuple | atomic | Public API | covered | all built-in backend names are stable public tuple |
| oracle/test_atomic.py::test_run_invokes_coroutine_and_returns_value | atomic | Public API | covered | run calls coroutine function and returns result |
| oracle/test_atomic.py::test_run_rejects_unknown_backend | atomic | Public API | covered | run rejects unknown backend |
| oracle/test_atomic.py::test_current_time_available_inside_event_loop[asyncio] | atomic | Product State Model | covered | running backend projection exposes monotonic clock |
| oracle/test_atomic.py::test_sleep_until_past_deadline_returns_promptly[asyncio] | atomic | Public API | covered | sleep_until past deadline returns promptly |
| oracle/test_atomic.py::test_move_on_after_suppresses_own_timeout[asyncio] | atomic | Public API | covered | move_on_after suppresses own timeout |
| oracle/test_atomic.py::test_fail_after_raises_timeout_error[asyncio] | atomic | Public API | covered | fail_after raises TimeoutError on own deadline |
| oracle/test_integration.py::test_effective_deadline_reflects_timeout_scope[asyncio] | integration | Cross-View Invariants | covered | timeout scope visible through current_effective_deadline |
| oracle/test_integration.py::test_task_group_waits_for_child_result_side_effect[asyncio] | integration | Public API | covered | task group waits for child task before exit |
| oracle/test_integration.py::test_task_group_start_returns_started_value[asyncio] | integration | Cross-View Invariants | covered | TaskGroup.start returns started value |
| oracle/test_integration.py::test_task_handle_projection_matches_started_and_returned_values[asyncio] | integration | Product State Model | covered | task group start value, awaited result and TaskHandle return_value expose one child task state |
| oracle/test_atomic.py::test_memory_stream_send_receive_one_item[asyncio] | atomic | Streams and Networking | covered | memory stream sends one object to receiver |
| oracle/test_atomic.py::test_memory_stream_nowait_would_block_when_empty[asyncio] | atomic | Error Semantics | covered | empty nowait receive raises WouldBlock |
| oracle/test_integration.py::test_memory_stream_close_all_receive_clones_breaks_send[asyncio] | integration | Cross-View Invariants | covered | closing all receive clones breaks later sends |
| oracle/test_integration.py::test_memory_stream_async_iteration_finishes_after_send_close[asyncio] | integration | Streams and Networking | covered | async iteration terminates after send close and drain |
| oracle/test_atomic.py::test_buffered_receive_exactly_reads_across_chunks[asyncio] | atomic | Streams and Networking | covered | buffered exact read crosses chunks |
| oracle/test_atomic.py::test_buffered_receive_until_returns_before_delimiter[asyncio] | atomic | Streams and Networking | covered | buffered delimiter read returns prefix |
| oracle/test_atomic.py::test_buffered_receive_exactly_incomplete_raises[asyncio] | atomic | Error Semantics | covered | buffered exact read raises IncompleteRead on EOF |
| oracle/test_atomic.py::test_text_send_stream_encodes_to_bytes[asyncio] | atomic | Streams and Networking | covered | text send stream encodes configured text |
| oracle/test_atomic.py::test_text_receive_stream_decodes_bytes[asyncio] | atomic | Streams and Networking | covered | text receive stream decodes configured bytes |
| oracle/test_integration.py::test_stapled_object_stream_closes_both_halves[asyncio] | integration | Streams and Networking | covered | stapled close closes both halves |
| oracle/test_atomic.py::test_open_file_writes_and_reads_text[asyncio] | atomic | Files, Processes and Workers | covered | open_file returns async file wrapper for disk IO |
| oracle/test_integration.py::test_wrap_file_closes_underlying_file[asyncio] | integration | Cross-View Invariants | covered | wrap_file close closes underlying file |
| oracle/test_atomic.py::test_async_path_read_write_roundtrip[asyncio] | atomic | Files, Processes and Workers | covered | Path async read/write round trip |
| oracle/test_integration.py::test_temporary_directory_context_removes_path[asyncio] | integration | Files, Processes and Workers | covered | temporary directory lifetime mirrors tempfile |
| oracle/test_integration.py::test_run_process_captures_stdout[asyncio] | integration | Files, Processes and Workers | covered | run_process captures stdout and return code |
| oracle/test_atomic.py::test_run_process_check_raises_called_process_error[asyncio] | atomic | Files, Processes and Workers | covered | run_process check raises CalledProcessError |
| oracle/test_integration.py::test_to_thread_copies_contextvars_without_back_propagation[asyncio] | integration | Cross-View Invariants | covered | to_thread copies context into worker without back-propagation |
| oracle/test_integration.py::test_from_thread_run_sync_uses_originating_loop[asyncio] | integration | Cross-View Invariants | covered | from_thread run_sync uses originating loop token from worker |
| oracle/test_integration.py::test_event_wakes_waiter[asyncio] | integration | Synchronization, Typed Attributes and Low Level APIs | covered | Event wakes waiting tasks |
| oracle/test_atomic.py::test_lock_released_by_non_owner_raises[asyncio] | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Lock ownership precondition raises runtime error |
| oracle/test_atomic.py::test_condition_notify_requires_lock[asyncio] | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Condition notify requires lock ownership |
| oracle/test_atomic.py::test_capacity_limiter_rejects_double_borrow[asyncio] | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | CapacityLimiter borrower holds at most one token |
| oracle/test_atomic.py::test_runvar_set_get_reset_within_run[asyncio] | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | RunVar set/get/reset are run-local |
| oracle/test_atomic.py::test_functools_reduce_consumes_async_iterable[asyncio] | atomic | Async Helpers and Testing | covered | async reduce consumes async iterable and awaits reducer |
| oracle/test_atomic.py::test_functools_cache_reuses_coroutine_result[asyncio] | atomic | Async Helpers and Testing | covered | cache reuses coroutine result |
| oracle/test_atomic.py::test_functools_lru_cache_honors_arguments[asyncio] | atomic | Async Helpers and Testing | covered | lru_cache caches by argument key |
| oracle/test_atomic.py::test_lowlevel_checkpoint_allows_progress[asyncio] | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | checkpoint yields through backend |
| oracle/test_atomic.py::test_current_token_available_inside_run[asyncio] | atomic | Product State Model | covered | current_token exposes event-loop token inside run |
| oracle/test_atomic.py::test_memory_nowait_closed_same_end_raises_closed[asyncio] | atomic | Error Semantics | covered | using closed same stream end raises ClosedResourceError |
| oracle/test_integration.py::test_representative_memory_timeout_workflow[asyncio] | system_e2e | Representative Workflows | covered | memory object stream and timeout compose in workflow |
| oracle/test_integration.py::test_representative_task_start_and_cancel_workflow[asyncio] | system_e2e | Representative Workflows | covered | task start readiness and cancellation workflow |
| oracle/test_integration.py::test_representative_task_memory_file_workflow[asyncio] | system_e2e | Representative Workflows | covered | task group, memory stream, file IO and timeout compose |
| oracle/test_atomic.py::test_current_time_requires_event_loop | atomic | Error Semantics | covered | current_time raises NoEventLoopError outside loop |
| oracle/test_atomic.py::test_cancelled_class_requires_event_loop | atomic | Error Semantics | covered | cancelled exception class requires event loop |
| oracle/test_atomic.py::test_from_thread_run_sync_foreign_thread_requires_token | atomic | Error Semantics | covered | foreign thread entry without token raises NoEventLoopError |
| oracle/test_atomic.py::test_semaphore_rejects_invalid_initial_value | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Semaphore rejects invalid initial value |
| oracle/test_atomic.py::test_resource_guard_rejects_concurrent_entry | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | ResourceGuard raises BusyResourceError for concurrent use |
| oracle/test_atomic.py::test_current_token_requires_event_loop | atomic | Error Semantics | covered | current_token requires supported event loop |
