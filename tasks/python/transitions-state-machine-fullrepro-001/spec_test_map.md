# Specification coverage map

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `oracle/test_atomic.py::test_state_exposes_its_public_name_and_value[ready]` | atomic | ### Core objects | covered | public State name/value behavior |
| `oracle/test_atomic.py::test_state_exposes_its_public_name_and_value[waiting]` | atomic | ### Core objects | covered | public State name/value behavior |
| `oracle/test_atomic.py::test_state_exposes_its_public_name_and_value[done]` | atomic | ### Core objects | covered | public State name/value behavior |
| `oracle/test_atomic.py::test_state_rejects_unknown_callback_phase` | atomic | ### Core objects | covered | public error behavior |
| `oracle/test_atomic.py::test_transition_rejects_unknown_callback_phase` | atomic | ### Core objects | covered | public error behavior |
| `oracle/test_atomic.py::test_machine_constructs_itself_as_its_default_model` | atomic | ### Machine construction | covered | default model is the machine instance |
| `oracle/test_atomic.py::test_machine_accepts_documented_state_dictionary_definitions` | atomic | ### Machine construction | covered | documented state dictionaries define usable states |
| `oracle/test_atomic.py::test_overview_allows_the_machine_to_serve_as_its_own_model` | atomic | ## Product Overview | covered | machine can itself receive state and trigger helpers |
| `oracle/test_atomic.py::test_unknown_state_lookup_raises_value_error[missing]` | atomic | ## Error Semantics | covered | unknown state error type |
| `oracle/test_atomic.py::test_unknown_state_lookup_raises_value_error[other]` | atomic | ## Error Semantics | covered | unknown state error type |
| `oracle/test_atomic.py::test_unknown_state_lookup_raises_value_error[not_registered]` | atomic | ## Error Semantics | covered | unknown state error type |
| `oracle/test_atomic.py::test_invalid_trigger_obeys_ignore_invalid_triggers[False]` | atomic | ## Error Semantics | covered | invalid-trigger behavior |
| `oracle/test_atomic.py::test_invalid_trigger_obeys_ignore_invalid_triggers[True]` | atomic | ## Error Semantics | covered | invalid-trigger behavior |
| `oracle/test_atomic.py::test_trigger_name_cannot_equal_model_attribute` | atomic | ## Error Semantics | covered | configuration failure type |
| `oracle/test_atomic.py::test_factory_supported_combinations_construct_machine[bad0]` | atomic | ### Extension machines | covered | supported factory selection |
| `oracle/test_atomic.py::test_factory_supported_combinations_construct_machine[bad1]` | atomic | ### Extension machines | covered | supported factory selection |
| `oracle/test_atomic.py::test_factory_supported_combinations_construct_machine[bad2]` | atomic | ### Extension machines | covered | supported factory selection |
| `oracle/test_atomic.py::test_tag_feature_exposes_documented_tag_predicates[initial]` | atomic | ### State features and typed definitions | covered | documented tag predicates |
| `oracle/test_atomic.py::test_tag_feature_exposes_documented_tag_predicates[approved]` | atomic | ### State features and typed definitions | covered | documented tag predicates |
| `oracle/test_atomic.py::test_tag_feature_exposes_documented_tag_predicates[failed]` | atomic | ### State features and typed definitions | covered | documented tag predicates |
| `oracle/test_atomic.py::test_may_trigger_reports_unknown_names_as_false_when_invalid_triggers_are_ignored[missing]` | atomic | ### Transitions and dynamic helpers | covered | public may_trigger error policy |
| `oracle/test_atomic.py::test_may_trigger_reports_unknown_names_as_false_when_invalid_triggers_are_ignored[unknown]` | atomic | ### Transitions and dynamic helpers | covered | public may_trigger error policy |
| `oracle/test_atomic.py::test_may_trigger_reports_unknown_names_as_false_when_invalid_triggers_are_ignored[not_registered]` | atomic | ### Transitions and dynamic helpers | covered | public may_trigger error policy |
| `oracle/test_integration.py::test_machine_creates_the_default_initial_state_for_a_later_model` | integration | ### Machine construction | covered | omitted initial creates the documented initial state |
| `oracle/test_integration.py::test_add_model_requires_an_initial_state_when_machine_initial_is_none` | integration | ### Machine construction | covered | `initial=None` requires an explicit model initial state and raises ValueError when omitted |
| `oracle/test_integration.py::test_machine_custom_model_attribute_changes_state_helpers` | integration | ### Machine construction | covered | custom state attribute changes dynamic state helpers |
| `oracle/test_integration.py::test_overview_projects_machine_state_to_a_separate_application_object` | integration | ## Product Overview | covered | machine projects state to an application model |
| `oracle/test_integration.py::test_overview_keeps_multiple_registered_model_projections_independent` | integration | ## Product Overview | covered | one model transition does not change another model |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[A-B]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[B-C]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[C-D]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[cold-warm]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[warm-hot]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_trigger_updates_all_public_state_projections[idle-active]` | system_e2e | ## Cross-View Invariants | covered | trigger binds model state, registry, and helpers |
| `oracle/test_integration.py::test_automatic_transition_helper_changes_state[B]` | integration | ### Transitions and dynamic helpers | covered | automatic helper changes documented state |
| `oracle/test_integration.py::test_automatic_transition_helper_changes_state[C]` | integration | ### Transitions and dynamic helpers | covered | automatic helper changes documented state |
| `oracle/test_integration.py::test_automatic_transition_helper_changes_state[D]` | integration | ### Transitions and dynamic helpers | covered | automatic helper changes documented state |
| `oracle/test_integration.py::test_automatic_transition_helper_changes_state[E]` | integration | ### Transitions and dynamic helpers | covered | automatic helper changes documented state |
| `oracle/test_integration.py::test_conditions_control_result_without_wrong_state_change[True]` | integration | ### Callback and event behavior | covered | condition result and state preservation |
| `oracle/test_integration.py::test_conditions_control_result_without_wrong_state_change[False]` | integration | ### Callback and event behavior | covered | condition result and state preservation |
| `oracle/test_integration.py::test_representative_workflow_advances_hot_matter` | system_e2e | ## Representative Workflow | covered | documented solid-to-liquid conditional workflow |
| `oracle/test_integration.py::test_representative_workflow_keeps_cold_matter_solid` | system_e2e | ## Representative Workflow | covered | failed workflow condition preserves source state |
| `oracle/test_integration.py::test_representative_workflow_rejects_melting_from_an_unrelated_state` | system_e2e | ## Representative Workflow | covered | invalid workflow trigger raises documented error |
| `oracle/test_integration.py::test_add_model_honors_requested_initial_state[A-B]` | integration | ### Machine configuration and inspection | covered | public add_model initial contract |
| `oracle/test_integration.py::test_add_model_honors_requested_initial_state[B-C]` | integration | ### Machine configuration and inspection | covered | public add_model initial contract |
| `oracle/test_integration.py::test_add_model_honors_requested_initial_state[C-D]` | integration | ### Machine configuration and inspection | covered | public add_model initial contract |
| `oracle/test_integration.py::test_set_state_and_get_state_agree[A]` | integration | ## Cross-View Invariants | covered | set_state and registry agreement |
| `oracle/test_integration.py::test_set_state_and_get_state_agree[B]` | integration | ## Cross-View Invariants | covered | set_state and registry agreement |
| `oracle/test_integration.py::test_set_state_and_get_state_agree[C]` | integration | ## Cross-View Invariants | covered | set_state and registry agreement |
| `oracle/test_integration.py::test_reflexive_and_internal_transitions_preserve_state[=]` | integration | ### Transitions and dynamic helpers | covered | documented reflexive/internal semantics |
| `oracle/test_integration.py::test_reflexive_and_internal_transitions_preserve_state[None]` | integration | ### Transitions and dynamic helpers | covered | documented reflexive/internal semantics |
| `oracle/test_integration.py::test_ordered_transitions_follow_configured_cycle[True0]` | integration | ### Transitions and dynamic helpers | covered | documented ordered cycle |
| `oracle/test_integration.py::test_ordered_transitions_follow_configured_cycle[False]` | integration | ### Transitions and dynamic helpers | covered | documented ordered cycle |
| `oracle/test_integration.py::test_ordered_transitions_follow_configured_cycle[True1]` | integration | ### Transitions and dynamic helpers | covered | documented ordered cycle |
| `oracle/test_integration.py::test_remove_transition_removes_a_trigger_when_no_matches_remain[A]` | integration | ### Transitions and dynamic helpers | covered | remove_transition dynamic helper contract |
| `oracle/test_integration.py::test_remove_transition_removes_a_trigger_when_no_matches_remain[B]` | integration | ### Transitions and dynamic helpers | covered | remove_transition dynamic helper contract |
| `oracle/test_integration.py::test_dispatch_combines_results_for_every_registered_model[states0]` | system_e2e | ## Product State Model | covered | dispatch observes every registered model |
| `oracle/test_integration.py::test_dispatch_combines_results_for_every_registered_model[states1]` | system_e2e | ## Product State Model | covered | dispatch observes every registered model |
| `oracle/test_integration.py::test_dispatch_combines_results_for_every_registered_model[states2]` | system_e2e | ## Product State Model | covered | dispatch observes every registered model |
| `oracle/test_integration.py::test_callbacks_receive_direct_arguments_or_event_data[False]` | integration | ### Callback and event behavior | covered | callback argument delivery |
| `oracle/test_integration.py::test_callbacks_receive_direct_arguments_or_event_data[True]` | integration | ### Callback and event behavior | covered | callback argument delivery |
| `oracle/test_integration.py::test_locked_machine_public_import_supports_a_basic_transition` | integration | ## Installable Surface | covered | documented public extension import performs a state transition |
| `oracle/test_integration.py::test_async_machine_public_import_exposes_awaitable_event_helpers` | integration | ## Installable Surface | covered | documented public extension import exposes awaitable event helper |
| `oracle/test_integration.py::test_factory_public_import_selects_a_machine_that_can_transition` | integration | ## Installable Surface | covered | documented public factory import produces a usable machine |
| `oracle/test_integration.py::test_hierarchical_machine_enters_configured_initial_child[one]` | integration | ### Extension machines | covered | nested initial-child entry |
| `oracle/test_integration.py::test_hierarchical_machine_enters_configured_initial_child[two]` | integration | ### Extension machines | covered | nested initial-child entry |
| `oracle/test_integration.py::test_hierarchical_machine_enters_configured_initial_child[three]` | integration | ### Extension machines | covered | nested initial-child entry |
| `oracle/test_integration.py::test_hierarchical_exact_state_check_rejects_only_descendant_match` | integration | ### Extension machines | covered | exact versus descendant check |
| `oracle/test_integration.py::test_add_model_honors_each_requested_initial_state` | integration | ### Machine configuration and inspection | covered | public-API rewrite retained upstream behavioral intent |

Total: 69 | covered: 69 | excluded: 0
