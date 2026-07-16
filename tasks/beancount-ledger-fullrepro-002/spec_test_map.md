# Stage 3 Expanded Spec Test Map

Task: `beancount-ledger-fullrepro-001`

Oracle source: repaired_public_surface_expanded

Expanded from 28 to 51 public-surface tests during rescue. Reference gate is 51/51 and dummy gate is 0/51.

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `rewritten_public_surface_tests.py::test_root_api_exports_match_api_module` | repaired | atomic | ## Installable Surface | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_decimal_constructor_normalizes_public_inputs` | repaired | atomic | ### Numeric Values | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_amount_parsing_comparison_and_boolean_behavior` | repaired | atomic | ### Numeric Values | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_position_from_string_and_value_helpers` | repaired | atomic | ### Numeric Values | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_account_helpers_component_semantics` | repaired | atomic | ### Account Helpers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_account_type_helpers_default_signs_and_sorting` | repaired | atomic | ### Account Helpers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_directive_objects_metadata_and_filter_txns` | repaired | atomic | ### Directive Objects | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_getters_report_accounts_and_lifecycle` | repaired | atomic | ### Account and Entry Getters | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_operations_preserve_lots_and_currencies` | repaired | atomic | ### Inventories | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_add_amount_aggregates_and_removes_zero_lots` | repaired | atomic | ### Inventories | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_bool_requires_explicit_empty_check` | repaired | atomic | ## Error Semantics | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_price_map_lookup_latest_inverse_and_identity` | repaired | atomic | ### Prices and Conversions | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_conversion_helpers_use_prices_or_return_original_amount` | repaired | atomic | ### Prices and Conversions | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_returns_entries_errors_and_options` | repaired | integration | ### Loading Ledgers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_resolves_relative_includes_and_aggregates_options` | repaired | integration | ### Options Map | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_reports_missing_include_as_error` | repaired | integration | ## Error Semantics | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_balance_validation_error_contains_entry` | repaired | integration | ### Ledger Loading and Validation | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_doc_decorator_supplies_parsed_ledger_to_function` | repaired | integration | ### Loading Ledgers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_doc_expect_errors_accepts_invalid_docstring` | repaired | integration | ### Loading Ledgers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_loader_plugin_can_append_directive_via_public_contract` | repaired | integration | ### Plugins | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_plugin_import_failure_is_returned_as_load_error` | repaired | integration | ### Plugins | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_realize_builds_tree_and_account_postings_from_loaded_entries` | repaired | system_e2e | ## Cross-View Invariants | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_realize_min_accounts_creates_empty_requested_accounts` | repaired | integration | ### Realized Accounts | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_real_account_child_constraints_are_enforced` | repaired | atomic | ## Error Semantics | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_format_entry_omits_source_metadata_and_sorts_tags_links` | repaired | atomic | ### Printing | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_print_entry_and_print_entries_write_public_syntax` | repaired | atomic | ### Printing | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_same_day_ordering_balance_before_transaction_and_close_last` | repaired | system_e2e | ### Ledger Loading and Validation | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_configured_root_account_names_affect_parsing_and_signs` | repaired | system_e2e | ## Cross-View Invariants | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_account_validation_helpers_accept_components_and_reject_bad_names` | repaired | atomic | ### Account Helpers | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_amount_negation_and_currency_first_sorting` | repaired | atomic | ### Numeric Values | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_position_arithmetic_preserves_lot_cost` | repaired | atomic | ### Numeric Values | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_split_average_and_only_position_behavior` | repaired | integration | ### Inventories | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_add_position_and_add_inventory_accumulate_units` | repaired | integration | ### Inventories | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_inventory_reduce_does_not_mutate_original_inventory` | repaired | integration | ## Cross-View Invariants | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_price_map_duplicate_dates_keep_later_price_and_add_inverse` | repaired | integration | ### Prices and Conversions | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_get_weight_uses_cost_before_price_and_price_without_cost` | repaired | integration | ### Prices and Conversions | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_get_value_infers_value_currency_from_cost_or_price` | repaired | integration | ### Prices and Conversions | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_get_accounts_includes_pad_note_document_and_balance_accounts` | repaired | atomic | ### Account and Entry Getters | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_get_account_open_close_keeps_first_lifecycle_directives` | repaired | integration | ### Account and Entry Getters | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_duplicate_include_is_reported_as_load_error` | repaired | integration | ### Ledger Loading and Validation | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_unmatched_include_glob_is_returned_as_error` | repaired | integration | ### Ledger Loading and Validation | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_plugin_exception_is_converted_to_load_error` | repaired | integration | ### Plugins | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_plugin_systemexit_is_allowed_to_propagate` | repaired | integration | ### Plugins | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_realize_stores_account_attached_directives_and_pad_on_both_accounts` | repaired | system_e2e | ### Realized Accounts | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_realize_compute_balance_false_preserves_postings_without_balance` | repaired | system_e2e | ### Realized Accounts | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_format_entry_write_source_emits_source_comment` | repaired | atomic | ### Printing | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_parses_note_event_query_price_and_custom` | repaired | system_e2e | ### Ledger Syntax Objects | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_tags_and_links_store_without_markers_and_print_with_markers` | repaired | atomic | ## Cross-View Invariants | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_load_file_raw_plugin_mode_skips_standard_balance_validation` | repaired | system_e2e | ### Plugins and Transformations | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_price_lookup_is_as_of_requested_date` | repaired | integration | ### Prices and Market Value | covered | public-surface behavioral test; reference observed pass |
| `rewritten_public_surface_tests.py::test_realized_transaction_postings_preserve_parent_transaction` | repaired | system_e2e | ## Cross-View Invariants | covered | public-surface behavioral test; reference observed pass |

Total: 51 | kept (covered): 51 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 51
Covered by layer: atomic=22 | integration=21 | system_e2e=8

2026-07-02 rescue note: expanded corrected public-surface oracle from 28 to 51 tests; excluded three dummy-passing object-shape tests and replaced them with behavioral public loader/price/realization tests.
