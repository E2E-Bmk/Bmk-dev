# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_actor_decorator_returns_actor_and_registers_name` | atomic | Actors And Messages | covered |
| 2 | `oracle/test_atomic.py::test_actor_direct_call_returns_underlying_result` | atomic | Actors And Messages | covered |
| 3 | `oracle/test_atomic.py::test_actor_metadata_options_are_public` | atomic | Actors And Messages | covered |
| 4 | `oracle/test_atomic.py::test_actor_custom_actor_class_is_used` | atomic | Actors And Messages | covered |
| 5 | `oracle/test_atomic.py::test_invalid_queue_name_raises_value_error` | atomic | Broker And Worker | covered |
| 6 | `oracle/test_atomic.py::test_unsupported_actor_option_raises_value_error` | atomic | Actors And Messages | covered |
| 7 | `oracle/test_atomic.py::test_actor_message_contains_positional_and_keyword_arguments` | atomic | Actors And Messages | covered |
| 8 | `oracle/test_atomic.py::test_message_with_options_converts_callback_actor_to_name` | atomic | Middleware Lifecycle And Retry | covered |
| 9 | `oracle/test_atomic.py::test_message_with_options_rejects_non_actor_callback` | atomic | Middleware Lifecycle And Retry | covered |
| 10 | `oracle/test_atomic.py::test_message_args_are_normalized_to_tuple` | atomic | Actors And Messages | covered |
| 11 | `oracle/test_atomic.py::test_message_asdict_exposes_serializable_public_fields` | atomic | Actors And Messages | covered |
| 12 | `oracle/test_atomic.py::test_message_copy_replaces_fields_and_merges_options` | atomic | Actors And Messages | covered |
| 13 | `oracle/test_atomic.py::test_message_encode_decode_roundtrip` | atomic | Actors And Messages | covered |
| 14 | `oracle/test_atomic.py::test_invalid_message_bytes_raise_decode_error` | atomic | Actors And Messages | covered |
| 15 | `oracle/test_atomic.py::test_message_datetime_uses_utc_and_millisecond_timestamp` | atomic | Actors And Messages | covered |
| 16 | `oracle/test_atomic.py::test_json_encoder_roundtrips_message_data` | atomic | Encoders And Global Configuration | covered |
| 17 | `oracle/test_atomic.py::test_pickle_encoder_roundtrips_non_json_value` | atomic | Encoders And Global Configuration | covered |
| 18 | `oracle/test_atomic.py::test_global_encoder_can_be_replaced_and_restored` | atomic | Encoders And Global Configuration | covered |
| 19 | `oracle/test_atomic.py::test_stub_broker_declares_normal_and_delay_queues` | atomic | Broker And Worker | covered |
| 20 | `oracle/test_atomic.py::test_broker_declares_actor_and_can_lookup_it` | atomic | Broker And Worker | covered |
| 21 | `oracle/test_atomic.py::test_broker_unknown_actor_raises_actor_not_found` | atomic | Broker And Worker | covered |
| 22 | `oracle/test_atomic.py::test_stub_broker_consume_unknown_queue_raises_queue_not_found` | atomic | Broker And Worker | covered |
| 23 | `oracle/test_atomic.py::test_stub_broker_enqueue_unknown_queue_raises_queue_not_found` | atomic | Broker And Worker | covered |
| 24 | `oracle/test_atomic.py::test_stub_broker_join_unknown_queue_raises_queue_not_found` | atomic | Broker And Worker | covered |
| 25 | `oracle/test_atomic.py::test_message_proxy_forwards_fields_and_can_be_marked_failed` | atomic | Actors And Messages | covered |
| 26 | `oracle/test_atomic.py::test_message_proxy_exception_state_can_be_stuffed_and_cleared` | atomic | Actors And Messages | covered |
| 27 | `oracle/test_atomic.py::test_broker_add_middleware_exposes_actor_options` | atomic | Middleware Lifecycle And Retry | covered |
| 28 | `oracle/test_atomic.py::test_broker_middleware_missing_anchor_raises_value_error` | atomic | Middleware Lifecycle And Retry | covered |
| 29 | `oracle/test_atomic.py::test_base_middleware_has_empty_public_defaults` | atomic | Middleware Lifecycle And Retry | covered |
| 30 | `oracle/test_atomic.py::test_stub_result_backend_builds_readable_namespace_key` | atomic | Results | covered |
| 31 | `oracle/test_atomic.py::test_stub_result_backend_builds_legacy_hash_key` | atomic | Results | covered |
| 32 | `oracle/test_atomic.py::test_missing_result_marker_is_distinct_from_none` | atomic | Results | covered |
| 33 | `oracle/test_atomic.py::test_result_backend_missing_result_raises_result_missing` | atomic | Results | covered |
| 34 | `oracle/test_atomic.py::test_result_backend_stores_and_retrieves_result` | atomic | Results | covered |
| 35 | `oracle/test_atomic.py::test_result_backend_stored_exception_raises_result_failure` | atomic | Results | covered |
| 36 | `oracle/test_atomic.py::test_retry_exposes_requested_delay` | atomic | Middleware Lifecycle And Retry | covered |
| 37 | `oracle/test_atomic.py::test_barrier_requires_positive_party_count` | atomic | Rate Limiting | covered |
| 38 | `oracle/test_atomic.py::test_generic_actor_subclass_is_callable` | atomic | Actors And Messages | covered |
| 39 | `oracle/test_atomic.py::test_generic_actor_meta_options_are_forwarded` | atomic | Actors And Messages | covered |
| 40 | `oracle/test_atomic.py::test_generic_actor_abstract_base_is_not_registered_as_actor` | atomic | Actors And Messages | covered |
| 41 | `oracle/test_atomic.py::test_generic_actor_missing_perform_raises_not_implemented` | atomic | Actors And Messages | covered |
| 42 | `oracle/test_atomic.py::test_skip_message_is_a_middleware_error` | atomic | Middleware Lifecycle And Retry | covered |
| 43 | `oracle/test_atomic.py::test_retry_default_delay_can_be_none` | atomic | Middleware Lifecycle And Retry | covered |
| 44 | `oracle/test_integration.py::test_stub_broker_send_consume_and_ack_preserves_message_fields` | integration | Broker And Worker | covered |
| 45 | `oracle/test_integration.py::test_stub_broker_nack_moves_message_to_dead_letters` | integration | Middleware Lifecycle And Retry | covered |
| 46 | `oracle/test_integration.py::test_worker_processes_positional_and_keyword_actor_messages` | integration | Broker And Worker | covered |
| 47 | `oracle/test_integration.py::test_worker_processes_actor_on_custom_queue` | integration | Broker And Worker | covered |
| 48 | `oracle/test_integration.py::test_stub_broker_flush_removes_queued_messages_and_dead_letters` | integration | Middleware Lifecycle And Retry | covered |
| 49 | `oracle/test_integration.py::test_success_callback_receives_original_message_and_result` | integration | Middleware Lifecycle And Retry | covered |
| 50 | `oracle/test_integration.py::test_failure_callback_receives_exception_metadata` | integration | Middleware Lifecycle And Retry | covered |
| 51 | `oracle/test_integration.py::test_results_middleware_stores_actor_result_for_message` | integration | Results | covered |
| 52 | `oracle/test_integration.py::test_results_middleware_projects_actor_failure_as_result_failure` | integration | Results | covered |
| 53 | `oracle/test_integration.py::test_actor_without_results_option_has_no_retrievable_result` | integration | Results | covered |
| 54 | `oracle/test_integration.py::test_message_get_result_can_infer_backend_from_global_broker` | integration | Results | covered |
| 55 | `oracle/test_integration.py::test_pipeline_runs_messages_in_order_and_exposes_each_result` | integration | Pipelines And Groups | covered |
| 56 | `oracle/test_integration.py::test_pipeline_flattens_nested_pipeline_before_running` | integration | Pipelines And Groups | covered |
| 57 | `oracle/test_integration.py::test_pipeline_pipe_ignore_uses_receiving_message_arguments` | integration | Pipelines And Groups | covered |
| 58 | `oracle/test_integration.py::test_incomplete_pipeline_reports_missing_completion_without_worker` | integration | Pipelines And Groups | covered |
| 59 | `oracle/test_integration.py::test_group_runs_children_and_returns_results` | integration | Pipelines And Groups | covered |
| 60 | `oracle/test_integration.py::test_nested_group_returns_nested_result_lists` | integration | Pipelines And Groups | covered |
| 61 | `oracle/test_integration.py::test_group_wait_completes_after_worker_finishes` | integration | Pipelines And Groups | covered |
| 62 | `oracle/test_integration.py::test_group_completion_callback_runs_after_all_children` | integration | Pipelines And Groups | covered |
| 63 | `oracle/test_integration.py::test_group_callback_requires_group_callbacks_middleware` | integration | Pipelines And Groups | covered |
| 64 | `oracle/test_integration.py::test_group_of_pipelines_returns_pipeline_results` | integration | Pipelines And Groups | covered |
| 65 | `oracle/test_integration.py::test_custom_middleware_receives_declaration_and_processing_hooks` | integration | Middleware Lifecycle And Retry | covered |
| 66 | `oracle/test_integration.py::test_skip_message_hook_acknowledges_without_running_actor` | integration | Middleware Lifecycle And Retry | covered |
| 67 | `oracle/test_integration.py::test_retry_middleware_requeues_retry_exception_until_success` | integration | Middleware Lifecycle And Retry | covered |
| 68 | `oracle/test_integration.py::test_max_retries_zero_moves_failed_actor_to_dead_letters` | integration | Middleware Lifecycle And Retry | covered |
| 69 | `oracle/test_integration.py::test_pickle_encoder_integrates_with_broker_message_processing` | integration | Encoders And Global Configuration | covered |
| 70 | `oracle/test_integration.py::test_result_backend_uses_message_identity_across_store_and_get` | integration | Results | covered |
| 71 | `oracle/test_integration.py::test_barrier_completes_after_all_parties_signal` | integration | Rate Limiting | covered |
| 72 | `oracle/test_integration.py::test_concurrent_rate_limiter_releases_slot_after_context` | integration | Rate Limiting | covered |
| 73 | `oracle/test_integration.py::test_global_broker_setter_connects_actor_and_composition` | integration | Broker And Worker | covered |
| 74 | `oracle/test_integration.py::test_stub_broker_consumer_rejects_missing_message_queue_consistently` | integration | Broker And Worker | covered |
| 75 | `oracle/test_integration.py::test_actor_send_with_timedelta_delay_encodes_delay_metadata` | integration | Actors And Messages | covered |

final_scoreable: 75
