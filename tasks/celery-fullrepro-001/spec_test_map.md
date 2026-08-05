# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_app_exposes_main_name_and_default_conf` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_app_constructor_applies_broker_and_backend_configuration` | atomic | Installable Surface | covered |
| 3 | `oracle/test_atomic.py::test_conf_update_preserves_and_overrides_public_settings` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_add_defaults_accepts_a_mapping` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_add_defaults_accepts_a_callable` | atomic | Product State Model | covered |
| 6 | `oracle/test_atomic.py::test_config_from_cmdline_parses_typed_values` | atomic | Installable Surface | covered |
| 7 | `oracle/test_atomic.py::test_task_decorator_registers_a_named_task` | atomic | Installable Surface | covered |
| 8 | `oracle/test_atomic.py::test_task_decorator_preserves_callable_metadata` | atomic | Cross-View Invariants | covered |
| 9 | `oracle/test_atomic.py::test_task_decorator_accepts_execution_options` | atomic | Installable Surface | covered |
| 10 | `oracle/test_atomic.py::test_task_registry_contains_only_registered_public_task_names` | atomic | Cross-View Invariants | covered |
| 11 | `oracle/test_atomic.py::test_direct_task_call_executes_inline` | atomic | Representative Workflows | covered |
| 12 | `oracle/test_atomic.py::test_delay_returns_successful_eager_result` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_apply_returns_eager_result_with_success_state` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_apply_async_uses_explicit_task_id` | atomic | Scope | covered |
| 15 | `oracle/test_atomic.py::test_bound_task_sees_eager_request_context` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_task_signature_contains_task_args_kwargs_and_options` | atomic | Cross-View Invariants | covered |
| 17 | `oracle/test_atomic.py::test_signature_shortcut_creates_public_signature` | atomic | Installable Surface | covered |
| 18 | `oracle/test_atomic.py::test_signature_merge_prepends_args_and_overlays_kwargs` | atomic | Cross-View Invariants | covered |
| 19 | `oracle/test_atomic.py::test_signature_set_returns_self_with_updated_options` | atomic | Installable Surface | covered |
| 20 | `oracle/test_atomic.py::test_immutable_signature_rejects_new_arguments` | atomic | Product State Model | covered |
| 21 | `oracle/test_atomic.py::test_signature_clone_does_not_mutate_original_options` | atomic | Cross-View Invariants | covered |
| 22 | `oracle/test_atomic.py::test_signature_round_trip_from_mapping` | atomic | Cross-View Invariants | covered |
| 23 | `oracle/test_atomic.py::test_signature_serializes_as_a_plain_mapping` | atomic | Installable Surface | covered |
| 24 | `oracle/test_atomic.py::test_task_apply_async_preserves_routing_metadata_in_signature` | atomic | Cross-View Invariants | covered |
| 25 | `oracle/test_atomic.py::test_eager_success_result_exposes_metadata` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_eager_failure_result_records_failure_state` | atomic | Error Semantics | covered |
| 27 | `oracle/test_atomic.py::test_failed_result_get_can_suppress_propagation` | atomic | Error Semantics | covered |
| 28 | `oracle/test_atomic.py::test_failed_result_get_propagates_by_default` | atomic | Error Semantics | covered |
| 29 | `oracle/test_atomic.py::test_eager_result_revoke_changes_state` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_async_result_reads_stored_eager_metadata` | atomic | Product State Model | covered |
| 31 | `oracle/test_atomic.py::test_ignore_result_avoids_a_stored_backend_value` | atomic | Product State Model | covered |
| 32 | `oracle/test_atomic.py::test_state_sets_classify_ready_and_exception_states` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_state_precedence_orders_success_above_started` | atomic | Cross-View Invariants | covered |
| 34 | `oracle/test_atomic.py::test_group_signature_exposes_member_signatures` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_chain_signature_exposes_ordered_tasks` | atomic | Product State Model | covered |
| 36 | `oracle/test_atomic.py::test_chord_signature_exposes_header_and_body` | atomic | Product State Model | covered |
| 37 | `oracle/test_atomic.py::test_group_apply_returns_group_result` | atomic | Representative Workflows | covered |
| 38 | `oracle/test_atomic.py::test_chain_apply_returns_final_eager_result` | atomic | Representative Workflows | covered |
| 39 | `oracle/test_atomic.py::test_chord_length_hint_counts_header_tasks` | atomic | Product State Model | covered |
| 40 | `oracle/test_atomic.py::test_periodic_task_projection_records_signature_and_schedule` | atomic | Product State Model | covered |
| 41 | `oracle/test_atomic.py::test_task_request_execution_options_are_publicly_projected` | atomic | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_configured_app_registers_and_executes_a_task` | integration | Representative Workflows | covered |
| 43 | `oracle/test_integration.py::test_task_options_flow_into_eager_invocation` | integration | Representative Workflows | covered |
| 44 | `oracle/test_integration.py::test_bound_task_workflow_returns_context_and_stored_result` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_direct_and_delay_views_agree_on_task_value` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_signature_workflow_sets_options_then_executes` | integration | Representative Workflows | covered |
| 47 | `oracle/test_integration.py::test_cloned_signature_workflow_keeps_original_and_runs_clone` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_serialized_signature_round_trip_executes` | integration | Representative Workflows | covered |
| 49 | `oracle/test_integration.py::test_failure_workflow_exposes_state_and_nonpropagating_value` | integration | Error Semantics | covered |
| 50 | `oracle/test_integration.py::test_failure_workflow_can_propagate_then_revoke_separate_result` | integration | Error Semantics | covered |
| 51 | `oracle/test_integration.py::test_group_workflow_executes_distinct_member_tasks` | integration | Representative Workflows | covered |
| 52 | `oracle/test_integration.py::test_chain_workflow_passes_previous_value_to_next_task` | integration | Representative Workflows | covered |
| 53 | `oracle/test_integration.py::test_chord_workflow_collects_header_values` | integration | Representative Workflows | covered |
| 54 | `oracle/test_integration.py::test_group_then_aggregate_workflow_uses_group_result_values` | integration | Representative Workflows | covered |
| 55 | `oracle/test_integration.py::test_nested_canvas_workflow_preserves_task_order` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_backend_workflow_distinguishes_stored_and_ignored_results` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_result_metadata_workflow_links_task_name_and_state` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_state_workflow_classifies_success_failure_and_pending` | integration | Product State Model | covered |
| 59 | `oracle/test_integration.py::test_periodic_configuration_workflow_registers_named_schedule` | integration | Representative Workflows | covered |
| 60 | `oracle/test_integration.py::test_cli_version_projection_is_deterministic` | integration | Installable Surface | covered |
| 61 | `oracle/test_integration.py::test_cli_help_projection_lists_public_command_groups` | integration | Installable Surface | covered |
| 62 | `oracle/test_integration.py::test_cli_control_list_projection_is_service_free` | integration | Installable Surface | covered |
| 63 | `oracle/test_integration.py::test_cli_inspect_list_projection_is_service_free` | integration | Installable Surface | covered |
| 64 | `oracle/test_integration.py::test_bound_task_workflow_accepts_custom_headers_without_changing_value` | integration | Cross-View Invariants | covered |
| 65 | `oracle/test_integration.py::test_routing_workflow_keeps_queue_key_and_executes_payload` | integration | Representative Workflows | covered |
| 66 | `oracle/test_integration.py::test_default_routing_workflow_feeds_signature_and_eager_execution` | integration | Representative Workflows | covered |

final_scoreable: 66
