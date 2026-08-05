# Specification Test Map

Every physical test listed below is covered by the public behavior specification.

| Test | Layer | Spec Area | Status |
| --- | --- | --- | --- |
| `oracle/test_atomic.py::test_public_imports_expose_documented_runtime_classes` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_state_metadata_defaults_and_custom_values` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_declared_transition_becomes_event` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_initial_configuration_contains_initial_state` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_send_advances_to_next_state` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_event_method_call_matches_send` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_allowed_events_are_topology_based` | atomic | Cross-View Invariants | covered |
| `oracle/test_atomic.py::test_enabled_events_evaluate_guards` | atomic | Cross-View Invariants | covered |
| `oracle/test_atomic.py::test_conditional_transition_uses_first_passing_guard` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_conditional_transition_falls_back_when_guard_fails` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_unless_guard_blocks_until_predicate_is_false` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_validator_exception_propagates_and_keeps_state` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_prepare_event_enriches_action_arguments` | atomic | Representative Workflow | covered |
| `oracle/test_atomic.py::test_before_and_on_return_values_are_collected` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_single_callback_return_is_unwrapped` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_missing_callback_return_is_none` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_state_machine_rejects_unmatched_event_by_default` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_state_chart_ignores_unmatched_event_by_default` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_final_state_sets_termination_and_final_states` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_explicit_event_name_preserves_programmatic_id` | atomic | Public Import Surface | covered |
| `oracle/test_atomic.py::test_from_any_creates_global_transition` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_self_transition_runs_exit_enter_callbacks` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_internal_transition_skips_exit_enter_callbacks` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_model_method_can_supply_transition_action` | atomic | Representative Workflow | covered |
| `oracle/test_atomic.py::test_class_listener_factory_creates_fresh_listener` | atomic | Representative Workflow | covered |
| `oracle/test_atomic.py::test_two_root_initial_states_are_invalid` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_final_states_cannot_have_outgoing_transitions` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_unreachable_state_definition_is_invalid` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_named_callback_resolution_is_validated_on_instance_creation` | atomic | Error Semantics | covered |
| `oracle/test_atomic.py::test_donedata_requires_final_state` | atomic | Product State Model | covered |
| `oracle/test_atomic.py::test_invalid_listener_entries_are_rejected` | atomic | Error Semantics | covered |
| `oracle/test_integration.py::test_order_workflow_combines_guards_model_actions_and_listener` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_compound_state_enters_parent_and_initial_child` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_compound_child_transition_keeps_parent_active` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_compound_parent_transition_exits_children` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_compound_cross_boundary_callbacks_use_documented_order` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_parallel_state_enters_each_region_initial` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_parallel_region_transition_preserves_other_region` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_parallel_done_event_waits_for_all_regions` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_history_state_restores_previous_child` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_eventless_transition_fires_after_report_count_changes` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_done_state_event_advances_compound_parent` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_donedata_reaches_done_state_handler` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_error_execution_event_can_recover_from_action_error` | integration | Error Semantics | covered |
| `oracle/test_integration.py::test_raise_internal_event_completes_pipeline_in_one_send` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_on_callback_receives_previous_and_new_configuration` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_async_callback_can_be_used_from_synchronous_context` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_async_initial_state_activation_is_explicit_inside_event_loop` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_async_first_event_auto_activates_initial_state` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_enabled_event_projection_matches_guarded_send` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_runtime_listener_observes_events_after_attachment` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_listener_inheritance_appends_child_listeners` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_model_registered_as_listener_supplies_guard_and_action` | integration | Representative Workflow | covered |
| `oracle/test_integration.py::test_cross_boundary_transition_enters_sibling_compound_initial` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_descendant_transition_takes_priority_over_ancestor` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_transition_decorator_declares_event_with_inline_action` | integration | Product State Model | covered |
| `oracle/test_integration.py::test_markdown_projection_contains_same_declared_states_and_event` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_dependency_injection_projects_event_source_target_and_model` | integration | Cross-View Invariants | covered |
| `oracle/test_integration.py::test_validators_run_before_conditions` | integration | Error Semantics | covered |
| `oracle/test_integration.py::test_prepare_event_values_reach_guard_and_action` | integration | Representative Workflow | covered |

final_scoreable: 60
