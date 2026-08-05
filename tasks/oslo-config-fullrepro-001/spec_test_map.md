# Spec To Test Map

| # | Test nodeid | Layer | Spec section | Coverage |
| ---: | --- | --- | --- | --- |
| 1 | `oracle/test_atomic.py::test_opt_exposes_public_metadata` | atomic | Product State Model | covered |
| 2 | `oracle/test_atomic.py::test_opt_group_exposes_public_metadata` | atomic | Product State Model | covered |
| 3 | `oracle/test_atomic.py::test_default_group_registration_projects_default_value` | atomic | Product State Model | covered |
| 4 | `oracle/test_atomic.py::test_group_registration_projects_attribute_mapping` | atomic | Product State Model | covered |
| 5 | `oracle/test_atomic.py::test_cli_bool_option_sets_true` | atomic | Scope | covered |
| 6 | `oracle/test_atomic.py::test_cli_bool_inverse_sets_false` | atomic | Scope | covered |
| 7 | `oracle/test_atomic.py::test_grouped_cli_option_uses_group_prefix` | atomic | Scope | covered |
| 8 | `oracle/test_atomic.py::test_default_ini_values_are_typed` | atomic | Product State Model | covered |
| 9 | `oracle/test_atomic.py::test_group_ini_values_are_typed` | atomic | Product State Model | covered |
| 10 | `oracle/test_atomic.py::test_command_line_value_precedes_config_file` | atomic | Product State Model | covered |
| 11 | `oracle/test_atomic.py::test_set_default_changes_application_default` | atomic | Product State Model | covered |
| 12 | `oracle/test_atomic.py::test_config_file_precedes_set_default` | atomic | Product State Model | covered |
| 13 | `oracle/test_atomic.py::test_set_override_precedes_config_file` | atomic | Product State Model | covered |
| 14 | `oracle/test_atomic.py::test_clear_override_restores_config_file_value` | atomic | Product State Model | covered |
| 15 | `oracle/test_atomic.py::test_list_option_parses_comma_separated_ini_value` | atomic | Product State Model | covered |
| 16 | `oracle/test_atomic.py::test_dict_option_parses_key_value_ini_value` | atomic | Product State Model | covered |
| 17 | `oracle/test_atomic.py::test_multistr_option_preserves_repeated_ini_values` | atomic | Product State Model | covered |
| 18 | `oracle/test_atomic.py::test_quoted_string_option_strips_config_quotes` | atomic | Product State Model | covered |
| 19 | `oracle/test_atomic.py::test_ini_substitution_uses_previously_defined_values` | atomic | Product State Model | covered |
| 20 | `oracle/test_atomic.py::test_required_option_missing_raises_required_opt_error` | atomic | Error Semantics | covered |
| 21 | `oracle/test_atomic.py::test_port_type_rejects_value_outside_bounds` | atomic | Error Semantics | covered |
| 22 | `oracle/test_atomic.py::test_uri_type_enforces_allowed_schemes` | atomic | Error Semantics | covered |
| 23 | `oracle/test_atomic.py::test_host_address_option_accepts_hostnames_and_ip_addresses` | atomic | Product State Model | covered |
| 24 | `oracle/test_atomic.py::test_choice_option_rejects_unlisted_value` | atomic | Error Semantics | covered |
| 25 | `oracle/test_atomic.py::test_default_location_is_application_default` | atomic | Product State Model | covered |
| 26 | `oracle/test_atomic.py::test_set_default_location_is_application_managed` | atomic | Product State Model | covered |
| 27 | `oracle/test_atomic.py::test_set_override_location_is_application_managed` | atomic | Product State Model | covered |
| 28 | `oracle/test_atomic.py::test_config_file_location_is_user_controlled` | atomic | Product State Model | covered |
| 29 | `oracle/test_atomic.py::test_command_line_location_is_user_controlled` | atomic | Product State Model | covered |
| 30 | `oracle/test_atomic.py::test_export_import_state_preserves_values_and_groups` | atomic | Cross-View Invariants | covered |
| 31 | `oracle/test_atomic.py::test_pickled_configopts_uses_exported_state` | atomic | Cross-View Invariants | covered |
| 32 | `oracle/test_atomic.py::test_list_all_sections_reports_parsed_sections` | atomic | Product State Model | covered |
| 33 | `oracle/test_atomic.py::test_generator_cli_writes_machine_readable_json` | atomic | Public Import Surface | covered |
| 34 | `oracle/test_atomic.py::test_generator_json_contains_option_metadata` | atomic | Product State Model | covered |
| 35 | `oracle/test_atomic.py::test_generator_cli_writes_machine_readable_yaml` | atomic | Public Import Surface | covered |
| 36 | `oracle/test_atomic.py::test_generator_cli_writes_ini_sample` | atomic | Public Import Surface | covered |
| 37 | `oracle/test_atomic.py::test_validator_cli_accepts_config_matching_opt_data` | atomic | Representative Workflow | covered |
| 38 | `oracle/test_integration.py::test_quickstart_grouped_config_uses_file_and_default` | integration | Cross-View Invariants | covered |
| 39 | `oracle/test_integration.py::test_precedence_chain_default_file_then_cli` | integration | Cross-View Invariants | covered |
| 40 | `oracle/test_integration.py::test_override_survives_state_export_and_import` | integration | Cross-View Invariants | covered |
| 41 | `oracle/test_integration.py::test_clearing_override_restores_user_location` | integration | Cross-View Invariants | covered |
| 42 | `oracle/test_integration.py::test_grouped_cli_value_projects_location_and_value` | integration | Cross-View Invariants | covered |
| 43 | `oracle/test_integration.py::test_collection_options_round_trip_through_state` | integration | Cross-View Invariants | covered |
| 44 | `oracle/test_integration.py::test_config_dir_files_override_config_file_in_sorted_order` | integration | Cross-View Invariants | covered |
| 45 | `oracle/test_integration.py::test_substitution_feeds_typed_list_projection` | integration | Cross-View Invariants | covered |
| 46 | `oracle/test_integration.py::test_location_projection_changes_with_source_precedence` | integration | Cross-View Invariants | covered |
| 47 | `oracle/test_integration.py::test_pickled_grouped_config_can_be_accessed_after_restore` | integration | Cross-View Invariants | covered |
| 48 | `oracle/test_integration.py::test_generator_json_and_yaml_share_option_names` | integration | Cross-View Invariants | covered |
| 49 | `oracle/test_integration.py::test_generated_yaml_opt_data_validates_matching_config` | integration | Cross-View Invariants | covered |
| 50 | `oracle/test_integration.py::test_validator_rejects_unknown_local_option` | integration | Cross-View Invariants | covered |
| 51 | `oracle/test_integration.py::test_validator_exclude_group_ignores_dynamic_group` | integration | Cross-View Invariants | covered |
| 52 | `oracle/test_integration.py::test_generator_ini_and_json_agree_on_sample_default` | integration | Cross-View Invariants | covered |
| 53 | `oracle/test_integration.py::test_generator_records_choices_and_typed_bounds` | integration | Cross-View Invariants | covered |
| 54 | `oracle/test_integration.py::test_generator_records_secret_and_advanced_flags` | integration | Cross-View Invariants | covered |
| 55 | `oracle/test_integration.py::test_generator_records_deprecated_replacement_projection` | integration | Cross-View Invariants | covered |
| 56 | `oracle/test_integration.py::test_validator_accepts_dest_name_for_hyphenated_option` | integration | Cross-View Invariants | covered |
| 57 | `oracle/test_integration.py::test_validator_check_defaults_accepts_matching_defaults` | integration | Cross-View Invariants | covered |
| 58 | `oracle/test_integration.py::test_generated_defaults_can_seed_configopts_registration` | integration | Cross-View Invariants | covered |
| 59 | `oracle/test_integration.py::test_generated_group_metadata_matches_registered_group_access` | integration | Cross-View Invariants | covered |
| 60 | `oracle/test_integration.py::test_configopts_sections_and_validator_exclusion_agree_for_dynamic_group` | integration | Cross-View Invariants | covered |
| 61 | `oracle/test_integration.py::test_state_and_generator_views_share_registered_group_names` | integration | Cross-View Invariants | covered |
| 62 | `oracle/test_integration.py::test_machine_readable_outputs_are_stable_for_same_generated_namespace` | integration | Cross-View Invariants | covered |

final_scoreable: 62
