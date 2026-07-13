# spec_test_map.md

oracle_version: 20260704T112154Z
filter/oracle_source: generated_only
source_carrier: tests/test_swe_e2e_dateparser_generated.py
scorer_isolation: --remove-path dateparser

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| tests/test_swe_e2e_dateparser_generated.py::test_parse_absolute_english_month_name | generated | atomic | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_numeric_default_mdy_order | generated | atomic | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_french_numeric_uses_locale_order_without_override | generated | atomic | ### Date Order and Language Order | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_explicit_date_order_overrides_locale_order | generated | atomic | ### Date Order and Language Order | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_locale_date_order_false_uses_configured_order | generated | atomic | ### Date Order and Language Order | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_custom_date_format_with_swapped_day_month | generated | atomic | ### Parser Selection, Formats, and Normalization | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_spanish_with_explicit_language | generated | atomic | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_default_languages_fallback | generated | atomic | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_custom_language_detector_for_top_level_parse | generated | integration | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_languages_argument_prevents_custom_detector_call | generated | integration | ### `parse` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_use_given_language_order_false_uses_default_priority | generated | atomic | ### Date Order and Language Order | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_use_given_language_order_true_preserves_caller_order | generated | atomic | ### Date Order and Language Order | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_relative_tomorrow_uses_relative_base_time | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_relative_yesterday_uses_relative_base_time | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_relative_weeks_ago_uses_relative_base | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_relative_future_days_uses_relative_base | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_month_name_uses_current_day_from_relative_base | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_dates_from_future_moves_month_forward | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_dates_from_past_moves_month_backward | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_day_first_for_missing_day | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_day_last_for_missing_day | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_month_first_for_year_only | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_prefer_month_last_for_year_only | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_strict_parsing_rejects_incomplete_month | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_require_month_rejects_year_only_input | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_require_day_rejects_month_year_input | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_require_all_parts_accepts_complete_date | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_timestamp_in_utc | generated | atomic | ### Timezone Behavior | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_no_spaces_time_when_parser_enabled | generated | atomic | ### Parser Selection, Formats, and Normalization | covered | v2 states explicitly selected no-spaces-time parses compact digit dates and that "121994" returns datetime(1994, 1, 2) |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_custom_parser_list_can_exclude_relative_time | generated | atomic | ### Incomplete and Relative Dates | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_unicode_normalization_true_accepts_unaccented_french | generated | atomic | ### Parser Selection, Formats, and Normalization | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_unicode_normalization_false_rejects_unaccented_french | generated | atomic | ### Parser Selection, Formats, and Normalization | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_timezone_abbreviation_returns_naive_when_requested | generated | atomic | ### Timezone Behavior | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_timezone_abbreviation_returns_aware_when_requested | generated | atomic | ### Timezone Behavior | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_timezone_setting_converts_to_target_zone | generated | atomic | ### Timezone Behavior | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_parse_input_timezone_converts_to_target_zone_with_tzinfo | generated | atomic | ### Timezone Behavior | covered | v2 requires TO_TIMEZONE on timezone-bearing input to return an aware converted datetime; assertion avoids provider-specific tzinfo attributes |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_returns_month_period_for_missing_day | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_returns_year_period_for_year_only | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_known_languages_selects_dutch_locale | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_known_languages_selects_german_locale | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_known_languages_rejects_outside_language | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_return_time_as_period | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_parser_date_formats_report_month_period | generated | atomic | ### `DateData` and `DateDataParser` | covered | asserts date_formats parses year/month and reports month period; avoids missing-day exact value |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_supports_dictionary_style_read | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_supports_dictionary_style_write | generated | atomic | ### `DateData` and `DateDataParser` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_finds_documented_satellite_date | generated | integration | ### `search_dates` | covered | asserts extracted datetime and parse agreement; does not require exact substring boundary |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_adds_detected_language_without_changing_datetime | generated | integration | ### `search_dates` | covered | asserts datetime, language payload, and parse agreement; does not require exact substring boundary |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_extracts_multiple_dates_in_order | generated | integration | ### `search_dates` | covered | asserts ordered extracted datetimes and parse agreement; does not require exact substring boundary |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_with_explicit_spanish_language | generated | integration | ### `search_dates` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_custom_language_detector | generated | integration | ### `search_dates` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_languages_argument_prevents_detector_call | generated | integration | ### `search_dates` | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_relative_and_absolute_with_fixed_base | generated | integration | ### `search_dates` | covered | asserts ordered relative/absolute datetimes under fixed base; avoids glue-word substring boundary |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_return_time_span_for_past_month | generated | integration | ### Search Time Spans | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_return_time_span_for_past_week_default_monday | generated | integration | ### Search Time Spans | covered | v2 defines past week as the completed prior week, Monday-through-Sunday by default, preserving RELATIVE_BASE time-of-day |
| tests/test_swe_e2e_dateparser_generated.py::test_search_dates_return_time_span_respects_sunday_week_start | generated | integration | ### Search Time Spans | covered | v2 defines DEFAULT_START_OF_WEEK=sunday as Sunday-through-Saturday for the completed prior week, preserving RELATIVE_BASE time-of-day |
| tests/test_swe_e2e_dateparser_generated.py::test_cross_view_parse_matches_date_data_parser | generated | system_e2e | ## Cross-View Invariants | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_cross_view_search_result_matches_direct_parse | generated | system_e2e | ## Cross-View Invariants | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_cross_view_add_detected_language_preserves_search_payload | generated | system_e2e | ## Cross-View Invariants | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_cross_view_timezone_parse_matches_date_data_parser | generated | system_e2e | ## Cross-View Invariants | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_cross_view_strict_parsing_none_matches_date_data_parser_none | generated | system_e2e | ## Cross-View Invariants | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_invalid_setting_name_raises_setting_validation_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_invalid_date_order_raises_setting_validation_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_unknown_parser_name_raises_setting_validation_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_invalid_languages_type_raises_type_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_unknown_language_raises_value_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_invalid_locales_type_raises_type_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_unknown_locale_raises_value_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_invalid_region_type_raises_type_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_use_given_order_without_languages_or_locales_raises_value_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_get_date_data_non_string_input_raises_type_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_unknown_key_read_raises_key_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |
| tests/test_swe_e2e_dateparser_generated.py::test_date_data_unknown_key_write_raises_key_error | generated | atomic | ## Error Semantics | covered | reference-observed public behavior |

## Coverage Summary

- ## Cross-View Invariants: 5
- ## Error Semantics: 12
- ### Date Order and Language Order: 5
- ### Incomplete and Relative Dates: 16
- ### Parser Selection, Formats, and Normalization: 4
- ### Search Time Spans: 3
- ### Timezone Behavior: 5
- ### `DateData` and `DateDataParser`: 9
- ### `parse`: 6
- ### `search_dates`: 7

## Layer Summary

- atomic: 55
- integration: 12
- system_e2e: 5

Total: 72 | kept (covered): 72 | spec_gap: 0 | source-only: 0 | excluded: 0 | final_scoreable: 72
