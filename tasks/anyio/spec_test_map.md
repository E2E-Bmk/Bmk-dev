# Spec Test Map - anyio Stage 3

<!-- oracle_source: upstream_plus_generated; scorer_isolation: direct reference pytest with PYTHONPATH to reference src; reference gate: 65/65 passed -->

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| filter/rewritten_upstream_tests.py::test_upstream_invalid_max_buffer | upstream | atomic | Streams and Networking | covered | memory stream rejects invalid buffer size |
| filter/rewritten_upstream_tests.py::test_upstream_negative_max_buffer | upstream | atomic | Streams and Networking | covered | memory stream rejects negative buffer size |
| filter/rewritten_upstream_tests.py::test_upstream_receive_then_send[asyncio] | upstream | integration | Streams and Networking | covered | zero-buffer send/receive rendezvous |
| filter/rewritten_upstream_tests.py::test_upstream_send_nowait_then_receive_nowait[asyncio] | upstream | atomic | Streams and Networking | covered | nowait FIFO delivery |
| filter/rewritten_upstream_tests.py::test_upstream_iterate_memory_stream[asyncio] | upstream | integration | Streams and Networking | covered | async iteration drains until send close |
| filter/rewritten_upstream_tests.py::test_upstream_closed_send_stream_errors[asyncio] | upstream | atomic | Error Semantics | covered | closed same end and clean EOF exceptions |
| filter/rewritten_upstream_tests.py::test_upstream_closed_receive_stream_errors[asyncio] | upstream | atomic | Error Semantics | covered | closed receive and broken opposite end exceptions |
| filter/rewritten_upstream_tests.py::test_upstream_cancel_receive_restores_nowait_state[asyncio] | upstream | integration | Cross-View Invariants | covered | cancelled receive does not consume later send slot |
| filter/rewritten_upstream_tests.py::test_upstream_clone_keeps_other_ends_open[asyncio] | upstream | integration | Cross-View Invariants | covered | clone lifecycle projections agree |
| filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_exactly[asyncio] | upstream | atomic | Streams and Networking | covered | buffered exact byte reads |
| filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_exactly_incomplete[asyncio] | upstream | atomic | Error Semantics | covered | IncompleteRead on early EOF |
| filter/rewritten_upstream_tests.py::test_upstream_buffered_receive_until[asyncio] | upstream | atomic | Streams and Networking | covered | delimiter reads return bytes before delimiter |
| filter/generated_tests.py::test_deprecated_worker_interpreter_alias_warns | generated | atomic | Installable Surface | covered | deprecated top-level spelling warns and aliases public class |
| filter/generated_tests.py::test_stream_file_public_classes_are_importable | generated | atomic | Installable Surface | covered | public stream file classes and attributes import from documented module |
| filter/generated_tests.py::test_abc_public_resource_and_task_types_are_importable | generated | atomic | Installable Surface | covered | public ABC resource/task types import from documented module |
| filter/generated_tests.py::test_available_backend_projection_contains_asyncio | generated | atomic | Public API | covered | available backends are subset of all built-in backends |
| filter/generated_tests.py::test_all_backends_public_tuple | generated | atomic | Public API | covered | all built-in backend names are stable public tuple |
| filter/generated_tests.py::test_run_invokes_coroutine_and_returns_value | generated | atomic | Public API | covered | run calls coroutine function and returns result |
| filter/generated_tests.py::test_run_rejects_unknown_backend | generated | atomic | Public API | covered | run rejects unknown backend |
| filter/generated_tests.py::test_current_time_available_inside_event_loop[asyncio] | generated | atomic | Product State Model | covered | running backend projection exposes monotonic clock |
| filter/generated_tests.py::test_sleep_until_past_deadline_returns_promptly[asyncio] | generated | atomic | Public API | covered | sleep_until past deadline returns promptly |
| filter/generated_tests.py::test_move_on_after_suppresses_own_timeout[asyncio] | generated | atomic | Public API | covered | move_on_after suppresses own timeout |
| filter/generated_tests.py::test_fail_after_raises_timeout_error[asyncio] | generated | atomic | Public API | covered | fail_after raises TimeoutError on own deadline |
| filter/generated_tests.py::test_effective_deadline_reflects_timeout_scope[asyncio] | generated | integration | Cross-View Invariants | covered | timeout scope visible through current_effective_deadline |
| filter/generated_tests.py::test_task_group_waits_for_child_result_side_effect[asyncio] | generated | integration | Public API | covered | task group waits for child task before exit |
| filter/generated_tests.py::test_task_group_start_returns_started_value[asyncio] | generated | integration | Cross-View Invariants | covered | TaskGroup.start returns started value |
| filter/generated_tests.py::test_task_handle_projection_matches_started_and_returned_values[asyncio] | generated | integration | Product State Model | covered | task group start value, awaited result and TaskHandle return_value expose one child task state |
| filter/generated_tests.py::test_memory_stream_send_receive_one_item[asyncio] | generated | atomic | Streams and Networking | covered | memory stream sends one object to receiver |
| filter/generated_tests.py::test_memory_stream_nowait_would_block_when_empty[asyncio] | generated | atomic | Error Semantics | covered | empty nowait receive raises WouldBlock |
| filter/generated_tests.py::test_memory_stream_close_all_receive_clones_breaks_send[asyncio] | generated | integration | Cross-View Invariants | covered | closing all receive clones breaks later sends |
| filter/generated_tests.py::test_memory_stream_async_iteration_finishes_after_send_close[asyncio] | generated | integration | Streams and Networking | covered | async iteration terminates after send close and drain |
| filter/generated_tests.py::test_buffered_receive_exactly_reads_across_chunks[asyncio] | generated | atomic | Streams and Networking | covered | buffered exact read crosses chunks |
| filter/generated_tests.py::test_buffered_receive_until_returns_before_delimiter[asyncio] | generated | atomic | Streams and Networking | covered | buffered delimiter read returns prefix |
| filter/generated_tests.py::test_buffered_receive_exactly_incomplete_raises[asyncio] | generated | atomic | Error Semantics | covered | buffered exact read raises IncompleteRead on EOF |
| filter/generated_tests.py::test_text_send_stream_encodes_to_bytes[asyncio] | generated | atomic | Streams and Networking | covered | text send stream encodes configured text |
| filter/generated_tests.py::test_text_receive_stream_decodes_bytes[asyncio] | generated | atomic | Streams and Networking | covered | text receive stream decodes configured bytes |
| filter/generated_tests.py::test_stapled_object_stream_closes_both_halves[asyncio] | generated | integration | Streams and Networking | covered | stapled close closes both halves |
| filter/generated_tests.py::test_open_file_writes_and_reads_text[asyncio] | generated | atomic | Files, Processes and Workers | covered | open_file returns async file wrapper for disk IO |
| filter/generated_tests.py::test_wrap_file_closes_underlying_file[asyncio] | generated | integration | Cross-View Invariants | covered | wrap_file close closes underlying file |
| filter/generated_tests.py::test_async_path_read_write_roundtrip[asyncio] | generated | atomic | Files, Processes and Workers | covered | Path async read/write round trip |
| filter/generated_tests.py::test_temporary_directory_context_removes_path[asyncio] | generated | integration | Files, Processes and Workers | covered | temporary directory lifetime mirrors tempfile |
| filter/generated_tests.py::test_run_process_captures_stdout[asyncio] | generated | integration | Files, Processes and Workers | covered | run_process captures stdout and return code |
| filter/generated_tests.py::test_run_process_check_raises_called_process_error[asyncio] | generated | atomic | Files, Processes and Workers | covered | run_process check raises CalledProcessError |
| filter/generated_tests.py::test_to_thread_copies_contextvars_without_back_propagation[asyncio] | generated | integration | Cross-View Invariants | covered | to_thread copies context into worker without back-propagation |
| filter/generated_tests.py::test_from_thread_run_sync_uses_originating_loop[asyncio] | generated | integration | Cross-View Invariants | covered | from_thread run_sync uses originating loop token from worker |
| filter/generated_tests.py::test_event_wakes_waiter[asyncio] | generated | integration | Synchronization, Typed Attributes and Low Level APIs | covered | Event wakes waiting tasks |
| filter/generated_tests.py::test_lock_released_by_non_owner_raises[asyncio] | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Lock ownership precondition raises runtime error |
| filter/generated_tests.py::test_condition_notify_requires_lock[asyncio] | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Condition notify requires lock ownership |
| filter/generated_tests.py::test_capacity_limiter_rejects_double_borrow[asyncio] | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | CapacityLimiter borrower holds at most one token |
| filter/generated_tests.py::test_runvar_set_get_reset_within_run[asyncio] | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | RunVar set/get/reset are run-local |
| filter/generated_tests.py::test_functools_reduce_consumes_async_iterable[asyncio] | generated | atomic | Async Helpers and Testing | covered | async reduce consumes async iterable and awaits reducer |
| filter/generated_tests.py::test_functools_cache_reuses_coroutine_result[asyncio] | generated | atomic | Async Helpers and Testing | covered | cache reuses coroutine result |
| filter/generated_tests.py::test_functools_lru_cache_honors_arguments[asyncio] | generated | atomic | Async Helpers and Testing | covered | lru_cache caches by argument key |
| filter/generated_tests.py::test_lowlevel_checkpoint_allows_progress[asyncio] | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | checkpoint yields through backend |
| filter/generated_tests.py::test_current_token_available_inside_run[asyncio] | generated | atomic | Product State Model | covered | current_token exposes event-loop token inside run |
| filter/generated_tests.py::test_memory_nowait_closed_same_end_raises_closed[asyncio] | generated | atomic | Error Semantics | covered | using closed same stream end raises ClosedResourceError |
| filter/generated_tests.py::test_representative_memory_timeout_workflow[asyncio] | generated | system_e2e | Representative Workflows | covered | memory object stream and timeout compose in workflow |
| filter/generated_tests.py::test_representative_task_start_and_cancel_workflow[asyncio] | generated | system_e2e | Representative Workflows | covered | task start readiness and cancellation workflow |
| filter/generated_tests.py::test_representative_task_memory_file_workflow[asyncio] | generated | system_e2e | Representative Workflows | covered | task group, memory stream, file IO and timeout compose |
| filter/generated_tests.py::test_current_time_requires_event_loop | generated | atomic | Error Semantics | covered | current_time raises NoEventLoopError outside loop |
| filter/generated_tests.py::test_cancelled_class_requires_event_loop | generated | atomic | Error Semantics | covered | cancelled exception class requires event loop |
| filter/generated_tests.py::test_from_thread_run_sync_foreign_thread_requires_token | generated | atomic | Error Semantics | covered | foreign thread entry without token raises NoEventLoopError |
| filter/generated_tests.py::test_semaphore_rejects_invalid_initial_value | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | Semaphore rejects invalid initial value |
| filter/generated_tests.py::test_resource_guard_rejects_concurrent_entry | generated | atomic | Synchronization, Typed Attributes and Low Level APIs | covered | ResourceGuard raises BusyResourceError for concurrent use |
| filter/generated_tests.py::test_current_token_requires_event_loop | generated | atomic | Error Semantics | covered | current_token requires supported event loop |

Total: 65 | kept (covered): 65 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 65