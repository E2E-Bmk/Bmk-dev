# Specification-to-Test Map

- oracle_version: `2026-07-20-native-v1`
- source: retained upstream cases rewritten onto public entry points
- mapping: `source_nodeid_map.json`

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| `oracle/test_atomic.py::test_constructor_rejects_missing_and_invalid_components` | atomic | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init_bad_input` |
| `oracle/test_atomic.py::test_constructor_defaults_and_explicit_components` | atomic | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init` |
| `oracle/test_atomic.py::test_constructor_preserves_fold_for_ambiguous_time` | atomic | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init_with_fold` |
| `oracle/test_atomic.py::test_repr_uses_arrow_wrapper` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_repr` |
| `oracle/test_atomic.py::test_str_uses_iso_format` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_str` |
| `oracle/test_atomic.py::test_hash_matches_equivalent_datetime` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_hash` |
| `oracle/test_atomic.py::test_clone_returns_equal_distinct_value` | atomic | Arrow Value Views; Cross-View Invariants | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_clone` |
| `oracle/test_atomic.py::test_unknown_attribute_raises_attribute_error` | atomic | Arrow Value Views; Error Semantics | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_getattr_base` |
| `oracle/test_atomic.py::test_week_attribute_uses_iso_week` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_getattr_week` |
| `oracle/test_atomic.py::test_quarter_attribute_covers_boundaries` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_getattr_quarter` |
| `oracle/test_atomic.py::test_datetime_component_attributes_are_exposed` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_getattr_dt_value` |
| `oracle/test_atomic.py::test_tzinfo_defaults_to_utc` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_tzinfo` |
| `oracle/test_atomic.py::test_naive_removes_timezone_without_changing_fields` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_naive` |
| `oracle/test_atomic.py::test_timestamp_matches_datetime_timestamp` | atomic | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestArrowAttribute::test_timestamp` |
| `oracle/test_integration.py::test_custom_factory_returns_custom_arrow_subclass` | integration | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_api.py::TestModule::test_factory` |
| `oracle/test_integration.py::test_constructor_normalizes_pytz_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init_pytz_timezone` |
| `oracle/test_integration.py::test_constructor_accepts_zoneinfo_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init_zoneinfo_timezone` |
| `oracle/test_integration.py::test_constructor_accepts_dateutil_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowInit::test_init_dateutil_timezone` |
| `oracle/test_integration.py::test_arrow_now_matches_local_time` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_now` |
| `oracle/test_integration.py::test_arrow_utcnow_is_utc` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_utcnow` |
| `oracle/test_integration.py::test_arrow_fromtimestamp_accepts_timezone_and_rejects_text` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromtimestamp` |
| `oracle/test_integration.py::test_arrow_utcfromtimestamp_is_utc_and_rejects_text` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_utcfromtimestamp` |
| `oracle/test_integration.py::test_arrow_fromdatetime_defaults_naive_input_to_utc` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromdatetime` |
| `oracle/test_integration.py::test_arrow_fromdatetime_preserves_input_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromdatetime_dt_tzinfo` |
| `oracle/test_integration.py::test_arrow_fromdatetime_accepts_explicit_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromdatetime_tzinfo_arg` |
| `oracle/test_integration.py::test_arrow_fromdate_uses_midnight_and_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromdate` |
| `oracle/test_integration.py::test_arrow_strptime_accepts_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_strptime` |
| `oracle/test_integration.py::test_arrow_fromordinal_validates_and_constructs` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_arrow.py::TestTestArrowFactory::test_fromordinal` |
| `oracle/test_integration.py::test_format_protocol_uses_arrow_tokens` | integration | Arrow Value Views; Representative Workflow | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_format` |
| `oracle/test_integration.py::test_bare_format_uses_default_pattern` | integration | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_bare_format` |
| `oracle/test_integration.py::test_empty_format_protocol_matches_str` | integration | Arrow Value Views | covered | public rewrite of `tests/test_arrow.py::TestTestArrowRepresentation::test_format_no_format_string` |
| `oracle/test_integration.py::test_factory_get_without_args_returns_current_utc` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_no_args` |
| `oracle/test_integration.py::test_factory_timestamp_matches_explicit_x_parse` | integration | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_factory.py::TestGet::test_timestamp_one_arg_no_arg` |
| `oracle/test_integration.py::test_factory_rejects_none` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_none` |
| `oracle/test_integration.py::test_factory_accepts_struct_time` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_struct_time` |
| `oracle/test_integration.py::test_factory_accepts_numeric_timestamps_and_rejects_numeric_strings` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_timestamp` |
| `oracle/test_integration.py::test_factory_normalizes_millisecond_and_microsecond_timestamps` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_expanded_timestamp` |
| `oracle/test_integration.py::test_factory_timestamp_accepts_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_timestamp_with_tzinfo` |
| `oracle/test_integration.py::test_factory_accepts_existing_arrow` | integration | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_arrow` |
| `oracle/test_integration.py::test_factory_accepts_datetime` | integration | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_datetime` |
| `oracle/test_integration.py::test_factory_accepts_date` | integration | Construction And Factory Behavior; Cross-View Invariants | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_date` |
| `oracle/test_integration.py::test_factory_accepts_tzinfo_as_current_time_request` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_tzinfo` |
| `oracle/test_integration.py::test_factory_accepts_dateparser_datetime` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_dateparser_datetime` |
| `oracle/test_integration.py::test_factory_accepts_tzinfo_keyword_without_positional_value` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_kwarg_tzinfo` |
| `oracle/test_integration.py::test_factory_accepts_timezone_name_and_rejects_unknown_name` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_kwarg_tzinfo_string` |
| `oracle/test_integration.py::test_factory_normalizes_whitespace_when_requested` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_kwarg_normalize_whitespace` |
| `oracle/test_integration.py::test_factory_datetime_timezone_keyword_replaces_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_datetime_tzinfo_kwarg` |
| `oracle/test_integration.py::test_factory_arrow_timezone_keyword_replaces_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_arrow_tzinfo_kwarg` |
| `oracle/test_integration.py::test_factory_date_timezone_keyword_sets_timezone` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_date_tzinfo_kwarg` |
| `oracle/test_integration.py::test_factory_iso_calendar_timezone_keyword_sets_timezone` | integration | Construction And Factory Behavior; Representative Workflow | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_iso_calendar_tzinfo_kwarg` |
| `oracle/test_integration.py::test_factory_accepts_iso_string` | integration | Construction And Factory Behavior; Cross-View Invariants; Representative Workflow | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_iso_str` |
| `oracle/test_integration.py::test_factory_accepts_iso_calendar_and_validates_shape` | integration | Construction And Factory Behavior; Error Semantics; Cross-View Invariants | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_iso_calendar` |
| `oracle/test_integration.py::test_factory_rejects_unknown_single_argument` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_other` |
| `oracle/test_integration.py::test_factory_rejects_boolean_timestamp` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_bool` |
| `oracle/test_integration.py::test_factory_accepts_decimal_timestamp` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_one_arg_decimal` |
| `oracle/test_integration.py::test_factory_datetime_and_tzinfo_pair` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_datetime_tzinfo` |
| `oracle/test_integration.py::test_factory_datetime_and_timezone_name_pair` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_datetime_tz_str` |
| `oracle/test_integration.py::test_factory_date_and_tzinfo_pair` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_date_tzinfo` |
| `oracle/test_integration.py::test_factory_date_and_timezone_name_pair` | integration | Construction And Factory Behavior | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_date_tz_str` |
| `oracle/test_integration.py::test_factory_rejects_datetime_with_invalid_timezone_object` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_datetime_other` |
| `oracle/test_integration.py::test_factory_rejects_date_with_invalid_timezone_object` | integration | Construction And Factory Behavior; Error Semantics | covered | public rewrite of `tests/test_factory.py::TestGet::test_two_args_date_other` |
| `oracle/test_integration.py::test_formatter_formats_combined_pattern` | integration | Token Formatting; Cross-View Invariants | covered | public rewrite of `tests/test_formatter.py::TestFormatterFormatToken::test_format` |
| `oracle/test_integration.py::test_formatter_year_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_year` |
| `oracle/test_integration.py::test_formatter_month_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_month` |
| `oracle/test_integration.py::test_formatter_day_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_day` |
| `oracle/test_integration.py::test_formatter_hour_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_hour` |
| `oracle/test_integration.py::test_formatter_minute_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_minute` |
| `oracle/test_integration.py::test_formatter_second_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_second` |
| `oracle/test_integration.py::test_formatter_fraction_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_sub_second` |
| `oracle/test_integration.py::test_formatter_timestamp_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_timestamp` |
| `oracle/test_integration.py::test_formatter_timezone_offset_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_timezone` |
| `oracle/test_integration.py::test_formatter_timezone_name_alaska` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_timezone_formatter[US/Alaska]` |
| `oracle/test_integration.py::test_formatter_timezone_name_utc` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_timezone_formatter[UTC]` |
| `oracle/test_integration.py::test_formatter_timezone_name_mariehamn` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_timezone_formatter[Europe/Mariehamn]` |
| `oracle/test_integration.py::test_formatter_am_pm_tokens` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_am_pm` |
| `oracle/test_integration.py::test_formatter_iso_week_token` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_week` |
| `oracle/test_integration.py::test_formatter_scans_tokens_inside_literal_text` | integration | Token Formatting | covered | public rewrite of `filter/rewritten_upstream_tests.py::test_nonsense` |
| `oracle/test_integration.py::test_formatter_bracket_escaping` | integration | Token Formatting; Representative Workflow | covered | public rewrite of `tests/test_formatter.py::TestFormatterFormatToken::test_escape` |
| `oracle/test_integration.py::test_builtin_atom_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_atom` |
| `oracle/test_integration.py::test_builtin_cookie_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_cookie` |
| `oracle/test_integration.py::test_builtin_rfc822_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc_822` |
| `oracle/test_integration.py::test_builtin_rfc850_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc_850` |
| `oracle/test_integration.py::test_builtin_rfc1036_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc_1036` |
| `oracle/test_integration.py::test_builtin_rfc1123_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc_1123` |
| `oracle/test_integration.py::test_builtin_rfc2822_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc_2822` |
| `oracle/test_integration.py::test_builtin_rfc3339_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc3339` |
| `oracle/test_integration.py::test_builtin_rfc3339_strict_format` | integration | Token Formatting | covered | public rewrite of `tests/test_formatter.py::TestFormatterBuiltinFormats::test_rfc3339_strict` |

Total: 87 | kept: 87 | spec_gap: 0 | source-only: 0 | excluded: 1815 | final_scoreable: 87
