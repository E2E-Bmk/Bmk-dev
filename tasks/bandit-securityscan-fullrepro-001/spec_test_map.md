# Final oracle spec-test map

oracle_version: `2026-07-11T18:13:58+08:00`

oracle_source: `generated_only`

reference: `PyCQA/bandit@c45446eaa30c4f28289c3b8ba9a955e1d78ba715`

isolation: scorer must use `--remove-path bandit`; console scripts are resolved from the selected project environment.

quota_check: all 32 exact H2/H3 headings meet floor; Cross-View=12, Error=12, Representative Workflows=6, every other heading >=3. Cases=61 within the 50-70 cap. Layers: atomic=24, integration=26, system_e2e=11.

| test_nodeid | source | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| `filter/generated_tests.py::test_package_rating_constants_are_public` | generated | atomic | `## Installable Surface`; `## Public API`; `### Plugin results and decorators` | covered | package exports |
| `filter/generated_tests.py::test_issue_preserves_supplied_plugin_result_fields` | generated | integration | `## Public API`; `### Plugin results and decorators`; `## Reports`; `### JSON and YAML`; `### Add a rule plugin` | covered | supplied Issue fields plus representation-neutral documented JSON CWE projection |
| `filter/generated_tests.py::test_issue_decodes_byte_text_as_utf8` | generated | atomic | `## Public API`; `### Plugin results and decorators`; `### Add a rule plugin` | covered | byte text semantics |
| `filter/generated_tests.py::test_public_decorators_accept_documented_forms` | generated | atomic | `## Installable Surface`; `## Public API`; `### Plugin results and decorators`; `### Extension entry contracts`; `### Add a rule plugin` | covered | decorator forms |
| `filter/generated_tests.py::test_rule_b101_assert_used` | generated | atomic | `## Product Overview`; `## Scope`; `## Documented Rule Detection`; `### General and application rules` | covered | B101 |
| `filter/generated_tests.py::test_rule_b102_exec_used` | generated | atomic | `## Product Overview`; `## Documented Rule Detection`; `### General and application rules` | covered | B102 |
| `filter/generated_tests.py::test_rule_b104_bind_all_interfaces` | generated | atomic | `## Product Overview`; `## Documented Rule Detection`; `### General and application rules` | covered | B104 |
| `filter/generated_tests.py::test_rule_b105_hardcoded_password` | generated | atomic | `## Scope`; `## Documented Rule Detection`; `### General and application rules` | covered | B105 |
| `filter/generated_tests.py::test_rule_b108_hardcoded_tmp_path` | generated | atomic | `## Documented Rule Detection`; `### General and application rules` | covered | B108 |
| `filter/generated_tests.py::test_rule_b110_try_except_pass` | generated | integration | `## Configuration and Suppression`; `## Documented Rule Detection`; `### General and application rules` | covered | B110/B112 false-setting bare/broad/narrow consistency |
| `filter/generated_tests.py::test_rule_b113_request_without_timeout` | generated | atomic | `## Documented Rule Detection`; `### General and application rules` | covered | B113 |
| `filter/generated_tests.py::test_rule_b301_pickle_deserialization` | generated | atomic | `## Scope`; `## Documented Rule Detection`; `### Blacklisted calls` | covered | B301 |
| `filter/generated_tests.py::test_rule_b303_weak_crypto_constructor` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted calls` | covered | B303 |
| `filter/generated_tests.py::test_rule_b307_eval` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted calls` | covered | B307 |
| `filter/generated_tests.py::test_rule_b311_random_generator` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted calls` | covered | B311 |
| `filter/generated_tests.py::test_rule_b401_telnet_import` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted imports` | covered | B401 |
| `filter/generated_tests.py::test_rule_b403_pickle_import` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted imports` | covered | B403 |
| `filter/generated_tests.py::test_rule_b404_subprocess_import` | generated | atomic | `## Documented Rule Detection`; `### Blacklisted imports` | covered | B404 |
| `filter/generated_tests.py::test_rule_b501_disabled_certificate_validation` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B501 |
| `filter/generated_tests.py::test_rule_b506_unsafe_yaml_load` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B506 |
| `filter/generated_tests.py::test_rule_b602_subprocess_shell_true` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B602 dynamic command |
| `filter/generated_tests.py::test_rule_b608_string_built_sql` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B608 |
| `filter/generated_tests.py::test_rule_b701_jinja_autoescape_false` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B701 |
| `filter/generated_tests.py::test_rule_b704_dynamic_markup` | generated | atomic | `## Documented Rule Detection`; `### Cryptography, injection, and framework rules` | covered | B704 |
| `filter/generated_tests.py::test_stdin_scan_reports_stdin_filename_and_status` | generated | integration | `## Scanning and Selection`; `## Invocation Protocol`; ### `bandit` | covered | stdin workflow |
| `filter/generated_tests.py::test_recursive_scan_discovers_nested_python` | generated | integration | `## Scanning and Selection`; `## Invocation Protocol`; ### `bandit` | covered | recursive discovery |
| `filter/generated_tests.py::test_cli_and_config_exclusions_are_additive` | generated | system_e2e | `## Scanning and Selection`; `## Configuration and Suppression`; `## Representative Workflows`; `### Configure, scan, and consume JSON` | covered | combined exclusions |
| `filter/generated_tests.py::test_tests_option_selects_only_requested_rules` | generated | integration | `## Scanning and Selection`; `## Configuration and Suppression`; ### `bandit` | covered | include selection |
| `filter/generated_tests.py::test_skips_option_removes_requested_rule` | generated | integration | `## Scanning and Selection`; `## Configuration and Suppression`; ### `bandit` | covered | skip selection |
| `filter/generated_tests.py::test_overlapping_tests_and_skips_exit_two` | generated | integration | `## Scanning and Selection`; `## Configuration and Suppression`; `## Error Semantics` | covered | overlap failure |
| `filter/generated_tests.py::test_high_threshold_filters_low_issue_but_preserves_metrics` | generated | system_e2e | `## Product State Model`; `## Scanning and Selection`; `## Reports`; `## Cross-View Invariants` | covered | delivery filter versus run metrics |
| `filter/generated_tests.py::test_bare_nosec_suppresses_issue_and_updates_metric` | generated | integration | `## Configuration and Suppression`; `## Product State Model`; `## Cross-View Invariants` | covered | nosec |
| `filter/generated_tests.py::test_selective_nosec_does_not_suppress_different_rule` | generated | integration | `## Configuration and Suppression`; `## Cross-View Invariants` | covered | selective nosec |
| `filter/generated_tests.py::test_ignore_nosec_restores_finding_and_resets_suppression` | generated | system_e2e | `## Configuration and Suppression`; `## Product State Model`; `## Cross-View Invariants` | covered | ignore nosec |
| `filter/generated_tests.py::test_syntax_error_is_skipped_not_reported_as_issue` | generated | system_e2e | `## Product State Model`; `## Error Semantics`; `## Cross-View Invariants`; `### Configure, scan, and consume JSON` | covered | skipped-file projection |
| `filter/generated_tests.py::test_missing_config_exits_two` | generated | integration | `## Configuration and Suppression`; `## Error Semantics`; `## Invocation Protocol`; ### `bandit` | covered | missing config |
| `filter/generated_tests.py::test_no_target_exits_two` | generated | atomic | `## Error Semantics`; `## Invocation Protocol`; ### `bandit` | covered | usage failure |
| `filter/generated_tests.py::test_exit_zero_keeps_findings_but_forces_success` | generated | system_e2e | `## Product State Model`; `## Error Semantics`; `## Cross-View Invariants`; `## Invocation Protocol`; ### `bandit` | covered | exit override |
| `filter/generated_tests.py::test_named_profile_replaces_top_level_tests_then_cli_adds` | generated | system_e2e | `## Scanning and Selection`; `## Configuration and Suppression`; `## Representative Workflows`; `### Configure, scan, and consume JSON` | covered | profile precedence |
| `filter/generated_tests.py::test_toml_tool_bandit_tests_are_loaded` | generated | integration | `## Configuration and Suppression`; `## Representative Workflows`; `### Configure, scan, and consume JSON` | covered | TOML config |
| `filter/generated_tests.py::test_json_report_has_semantic_issue_and_metric_fields` | generated | integration | `## Reports`; `### JSON and YAML`; `## Evaluation Notes` | covered | parsed JSON |
| `filter/generated_tests.py::test_yaml_and_json_reports_have_equal_issue_identity_and_metrics` | generated | system_e2e | `## Reports`; `### JSON and YAML`; `## Product State Model`; `## Cross-View Invariants`; `## Non-Goals`; `## Evaluation Notes` | covered | semantic parity, presentation ignored |
| `filter/generated_tests.py::test_csv_report_projects_semantic_issue_columns` | generated | integration | `## Reports`; `### CSV and XML`; `## Non-Goals`; `## Evaluation Notes` | covered | parsed CSV |
| `filter/generated_tests.py::test_xml_report_count_and_issue_identity` | generated | integration | `## Reports`; `### CSV and XML`; `## Non-Goals`; `## Evaluation Notes` | covered | parsed XML |
| `filter/generated_tests.py::test_sarif_report_projects_rule_result_and_metrics` | generated | integration | `## Reports`; `### SARIF`; `### Extension entry contracts` | covered | parsed SARIF |
| `filter/generated_tests.py::test_sarif_projects_skipped_file_as_error_notification` | generated | integration | `## Reports`; `### SARIF`; `## Error Semantics`; `## Cross-View Invariants` | covered | skipped-file notification |
| `filter/generated_tests.py::test_html_report_contains_escaped_semantic_issue` | generated | integration | `## Reports`; `### Human and custom formats`; `### Extension entry contracts` | covered | HTML semantic/escaping |
| `filter/generated_tests.py::test_text_report_exposes_issue_and_rating_semantics` | generated | integration | `## Reports`; `### Human and custom formats`; `## Non-Goals` | covered | case-insensitive text rating semantics without exact presentation |
| `filter/generated_tests.py::test_custom_report_expands_documented_fields` | generated | integration | `## Reports`; `### Human and custom formats` | covered | custom fields |
| `filter/generated_tests.py::test_cross_format_issue_count_agrees` | generated | system_e2e | `## Product State Model`; `## Reports`; `### JSON and YAML`; `### CSV and XML`; `### SARIF`; `## Cross-View Invariants` | covered | five parsed views |
| `filter/generated_tests.py::test_cross_format_threshold_removes_same_identity` | generated | system_e2e | `## Scanning and Selection`; `## Reports`; `### JSON and YAML`; `## Cross-View Invariants` | covered | threshold identity |
| `filter/generated_tests.py::test_per_file_metrics_sum_to_totals` | generated | integration | `## Product State Model`; `## Reports`; `### JSON and YAML`; `## Cross-View Invariants` | covered | metric invariant |
| `filter/generated_tests.py::test_baseline_suppresses_moved_issue_but_keeps_new_issue` | generated | system_e2e | `## Baselines`; `## Product State Model`; `## Representative Workflows`; `### Establish and apply a baseline`; `## Cross-View Invariants` | covered | baseline lifecycle |
| `filter/generated_tests.py::test_baseline_with_yaml_formatter_exits_two` | generated | integration | `## Baselines`; `## Error Semantics`; `### Establish and apply a baseline` | covered | capability error |
| `filter/generated_tests.py::test_malformed_readable_baseline_behaves_as_empty` | generated | integration | `## Baselines`; `## Error Semantics`; `### Establish and apply a baseline` | covered | malformed baseline |
| `filter/generated_tests.py::test_config_generator_no_action_returns_one` | generated | atomic | `## Installable Surface`; `## Error Semantics`; `## Invocation Protocol`; ### `bandit-config-generator` | covered | no-action status |
| `filter/generated_tests.py::test_config_generator_creates_parseable_profile` | generated | integration | `## Installable Surface`; `### Extension entry contracts`; `## Representative Workflows`; `## Invocation Protocol`; ### `bandit-config-generator` | covered | generated config |
| `filter/generated_tests.py::test_config_generator_refuses_existing_output` | generated | integration | `## Installable Surface`; `## Error Semantics`; `## Invocation Protocol`; ### `bandit-config-generator` | covered | overwrite failure |
| `filter/generated_tests.py::test_bandit_baseline_restores_current_commit` | generated | system_e2e | `## Baselines`; `## Representative Workflows`; `### Establish and apply a baseline`; `## Invocation Protocol`; ### `bandit-baseline` | covered | local Git workflow |
| `filter/generated_tests.py::test_bandit_baseline_rejects_non_repository` | generated | integration | `## Baselines`; `## Error Semantics`; `## Invocation Protocol`; ### `bandit-baseline` | covered | non-repository failure |
| `filter/generated_tests.py::test_bandit_baseline_rejects_dirty_repository` | generated | integration | `## Baselines`; `## Error Semantics`; `## Invocation Protocol`; ### `bandit-baseline` | covered | dirty repository failure |

Total: 61 | kept (covered): 61 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 61
