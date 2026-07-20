# Final Spec-Test Map

spec_version: `v2`  
oracle_version: `20260718T153732Z`  
oracle_count: 60  
distinct_test_functions: 60  
expanded_scoring_nodeids: 60  
by_layer: atomic=15, integration=34, system_e2e=11  
by_source: upstream=48, generated=12

## Heading Coverage Audit

| exact spec heading | scoreable | covered tests | quota/result |
|---|---|---:|---|
| Product Overview | no | 0 | descriptive overview |
| Scope | no | 0 | non-scoreable documentation section |
| Installable Surface | yes | 3 | PASS (floor 3) |
| Product State Model | yes | 3 | PASS (floor 3) |
| Public API | no | 0 | section container |
| Contract declarations | yes | 5 | PASS (floor 3) |
| Process state | yes | 3 | PASS (floor 3) |
| Introspection objects | yes | 3 | PASS (floor 3) |
| Runtime Contract Lifecycle | no | 0 | section container |
| Validator inputs and outcomes | yes | 3 | PASS (floor 3) |
| Values, results, and ordering | yes | 5 | PASS (floor 3) |
| Generators and asynchronous functions | yes | 3 | PASS (floor 3) |
| Exceptions and reasons | yes | 3 | PASS (floor 3) |
| Side-effect markers | yes | 3 | PASS (floor 3) |
| Class invariants | yes | 3 | PASS (floor 3) |
| Dispatch and inheritance | yes | 7 | PASS (floor 3) |
| Runtime metadata | yes | 3 | PASS (floor 3) |
| Error Semantics | yes | 5 | PASS (floor 5) |
| Cross-View Invariants | yes | 5 | PASS (floor 5) |
| Representative Workflow | yes | 3 | PASS (floor 3) |
| Non-Goals | no | 0 | non-scoreable documentation section |
| Invocation Protocol | no | 0 | out-of-scope invocation documentation |
| Environment | no | 0 | non-scoreable documentation section |
| Evaluation Notes | no | 0 | non-scoreable protocol section |

## Scoreable Tests

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_preserve_type_annotations | atomic | Contract declarations | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_preserve_docstring | atomic | Contract declarations | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_implies | atomic | Contract declarations | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_catch | atomic | Contract declarations | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_chained_contract_decorator | integration | Values, results, and ordering | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__pre | integration | Cross-View Invariants | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_unwrap | atomic | Introspection objects | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_custom_exception_and_message | integration | Cross-View Invariants | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_get_contracts__raises | atomic | Introspection objects | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_get_contracts__reason | atomic | Introspection objects | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__has | integration | Side-effect markers | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__multiple | integration | Runtime metadata | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__example | integration | Runtime metadata | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__inherit_class | system_e2e | Cross-View Invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_get_contracts__inherit_func | system_e2e | Cross-View Invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_match | integration | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_no_match | integration | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_match_default | integration | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_propagate_pre_contract_error | integration | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_dispatch_works_with_disabled_contracts | system_e2e | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_parameters_and_result_fulfill_constact | integration | Validator inputs and outcomes | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_simple_signature | atomic | Validator inputs and outcomes | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_recursive_contracts_ok | integration | Validator inputs and outcomes | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_example_is_not_triggered_in_runtime | atomic | Runtime metadata | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_example_does_not_break_iterator | integration | Generators and asynchronous functions | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_example_does_not_break_async | integration | Generators and asynchronous functions | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_inherit_one_parent | integration | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_inherit_multiple_parents | system_e2e | Dispatch and inheritance | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_has_inherit_and_merge | system_e2e | Cross-View Invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_setting_wrong_args_by_method_raises_error | integration | Class invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_chain_contracts_both_fulfill | integration | Class invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_patch_class_with_slots | integration | Class invariants | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_raises_exception | integration | Side-effect markers | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_raises_specified_exception | integration | Error Semantics | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_return_value_fulfils_contract | atomic | Values, results, and ordering | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_decorating_generator | integration | Generators and asynchronous functions | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_pre_contract_fulfilled | atomic | Values, results, and ordering | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_chain_all_contracts_fulfilled | integration | Values, results, and ordering | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_method_decoration_name_is_correct | atomic | Contract declarations | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_class_method_decorator_raises_error_on_contract_fail | integration | Values, results, and ordering | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_pure_silent | integration | Error Semantics | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_pure_safe | integration | Exceptions and reasons | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_raises_expects_function_to_raise_error | integration | Exceptions and reasons | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_safe | atomic | Exceptions and reasons | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_not_allow_print | integration | Side-effect markers | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_contract_state_switch_custom_param | system_e2e | Process state | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_contract_state_switch_default_param_async | system_e2e | Process state | covered | upstream; public-API behavioral check |
| oracle/test_integration.py::test_contract_state_switch_default_param_generator | system_e2e | Process state | covered | upstream; public-API behavioral check |
| oracle/test_atomic.py::test_generated_root_runtime_exports_are_usable | atomic | Installable Surface | covered | generated; Root runtime decorators, state controls, and helpers are callable and helpers return their documented values. |
| oracle/test_atomic.py::test_generated_root_exception_exports_match_decorator_failures | atomic | Installable Surface | covered | generated; Root pre and post decorators raise the corresponding exception classes exported from the root namespace. |
| oracle/test_integration.py::test_generated_introspection_namespace_operates_independently | integration | Installable Surface | covered | generated; The independently imported introspection namespace exposes its public objects and reads a decorated callable. |
| oracle/test_integration.py::test_generated_disabled_decoration_reappears_in_all_views | integration | Product State Model | covered | generated; A contract attached while disabled remains visible with custom exception metadata and enforces after enabling. |
| oracle/test_integration.py::test_generated_retained_contract_and_unwrap_survive_disable | integration | Product State Model | covered | generated; Disabling retains the same introspection wrapper and original callable while bypassing result enforcement. |
| oracle/test_integration.py::test_generated_inherited_precondition_matches_bound_metadata | integration | Product State Model | covered | generated; An inherited precondition both rejects a bound child call and appears as public metadata on that method. |
| oracle/test_integration.py::test_generated_sync_fee_lifecycle_workflow | system_e2e | Representative Workflow | covered | generated; A synchronous pre-and-ensure definition survives inspection, disablement, and restored enforcement. |
| oracle/test_integration.py::test_generated_async_result_lifecycle_workflow | system_e2e | Representative Workflow | covered | generated; An asynchronous postcondition remains visible while disabled and rejects an invalid awaited result after enabling. |
| oracle/test_integration.py::test_generated_exception_policy_lifecycle_workflow | system_e2e | Representative Workflow | covered | generated; An exception allow-list remains visible while disabled and wraps an undeclared exception after enabling. |
| oracle/test_integration.py::test_generated_custom_exception_class_and_instance_control_violation_type | integration | Error Semantics | covered | generated; Configured custom exception classes and instances determine the type raised by value contract violations. |
| oracle/test_integration.py::test_generated_reason_violation_preserves_cause_type | integration | Error Semantics | covered | generated; A failed matching reason raises its violation type with the original event type as cause. |
| oracle/test_integration.py::test_generated_permanent_transitions_raise_runtime_error_in_child | integration | Error Semantics | covered | generated; A child process observes RuntimeError for every forbidden transition after permanent removal. |

Total: 60 | kept (covered): 60 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 60
