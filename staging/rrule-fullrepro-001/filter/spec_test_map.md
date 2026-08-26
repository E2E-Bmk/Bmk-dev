# Specification coverage map — rrule-fullrepro-001

oracle_source: generated_only (all tests written against the spec with
expected values verified by running the pinned reference — probe binary,
three rounds, plus full suite runs on both the patched path and the
registry lock; upstream tests served as a behavioral checklist only — see
rewrite_audit.md).

Test IDs are `{crate}::{module path}::{function}` as reported by
cargo-nextest against the oracle workspace.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| `atomic::generated_all_cap_and_limited_flag` | atomic | ## Occurrence Iteration | covered | limited true iff the cap was hit, incl. exactly |
| `atomic::generated_all_unchecked_finite` | atomic | ## Occurrence Iteration | covered | uncapped collection of a finite set |
| `atomic::generated_build_wraps_single_rule_set` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | build = validate + single-rule set; errors propagate |
| `atomic::generated_builder_defaults` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | interval 1, wkst Monday, no count/until, empty lists |
| `atomic::generated_builder_getters_after_set` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | interval/count/until/week_start round through getters |
| `atomic::generated_bulk_setters_replace` | atomic | ## Set Composition | covered | set_rrules/set_rdates/set_exdates replace collections |
| `atomic::generated_by_month_setter_reports_numbers` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | Month values surface as 1-12 numbers |
| `atomic::generated_bymonthday_weekly_forbidden` | atomic | ## Validation Rules | covered | BYMONTHDAY under WEEKLY rejected; MONTHLY sibling ok |
| `atomic::generated_bysetpos_companion_secondly` | atomic | ## Validation Rules | covered | lone BYSETPOS fails only at SECONDLY |
| `atomic::generated_bysetpos_range_and_zero` | atomic | ## Validation Rules | covered | zero and out-of-range positions rejected |
| `atomic::generated_byweekno_yearly_only` | atomic | ## Validation Rules | covered | BYWEEKNO restricted to YEARLY |
| `atomic::generated_byyearday_frequency_rules` | atomic | ## Validation Rules | covered | BYYEARDAY forbidden for daily/weekly/monthly |
| `atomic::generated_count_zero_empty` | atomic | ## Occurrence Iteration | covered | count 0 contributes nothing |
| `atomic::generated_dst_ambiguous_earlier_offset` | atomic | ## Timezone and Daylight-Saving Behavior | covered | fall-back ambiguity picks the earlier offset |
| `atomic::generated_dst_gap_shift_daily` | atomic | ## Timezone and Daylight-Saving Behavior | covered | nonexistent local time shifts +1h on the gap day |
| `atomic::generated_dst_wallclock_daily` | atomic | ## Timezone and Daylight-Saving Behavior | covered | wall clock held; 23h real delta at spring-forward |
| `atomic::generated_dtstart_emitted_iff_matching` | atomic | ## Occurrence Iteration | covered | start emitted only when it matches the pattern |
| `atomic::generated_empty_set_behavior` | atomic | ## Set Composition | covered | empty set: empty stream, empty getters |
| `atomic::generated_exdate_instant_across_zones` | atomic | ## Set Composition | covered | exclusion matches by absolute instant |
| `atomic::generated_exdate_removes_every_instance` | atomic | ## Set Composition | covered | exclusion removes all duplicates at the instant |
| `atomic::generated_frequency_display_uppercase` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | all seven variants render RFC keywords |
| `atomic::generated_frequency_from_str_case_insensitive` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | case-insensitive parse; unknown keyword errs |
| `atomic::generated_interval_stepping` | atomic | ## Occurrence Iteration | covered | interval 2 daily and secondly across midnight |
| `atomic::generated_into_iter_ignores_window` | atomic | ## Occurrence Iteration | covered | direct iterator unbounded, ignores window |
| `atomic::generated_lists_sorted_deduped` | atomic | ## Normalization and Derived Properties | covered | BY lists sorted ascending, duplicates removed |
| `atomic::generated_monthday_zero_pruned` | atomic | ## Normalization and Derived Properties | covered | zero discarded, fill then applies |
| `atomic::generated_monthly_fill_from_start` | atomic | ## Normalization and Derived Properties | covered | BYMONTHDAY+time fills from the start instant |
| `atomic::generated_negative_monthday_hidden_but_active` | atomic | ## Normalization and Derived Properties | covered | getter/display hide it, iteration honors it |
| `atomic::generated_no_date_fill_with_byday_present` | atomic | ## Normalization and Derived Properties | covered | date selector suppresses the date fill |
| `atomic::generated_nweekday_constructor_forms` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | new(None/Some) selects Every/Nth |
| `atomic::generated_nweekday_display_notation` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | MO / 2TU / -1SU notation |
| `atomic::generated_nweekday_from_str` | atomic | ## Recurrence Vocabulary and Rule Construction | covered | notation parses back; invalid errs |
| `atomic::generated_occurrence_zone_by_source` | atomic | ## Timezone and Daylight-Saving Behavior | covered | rules yield the start zone; rdates keep their own |
| `atomic::generated_rdate_duplicates_preserved` | atomic | ## Set Composition | covered | equal extra dates both emitted |
| `atomic::generated_rdates_only_sorted` | atomic | ## Set Composition | covered | extra dates alone yield a sorted stream |
| `atomic::generated_rrule_parse_accepts_prefix` | atomic | ## Parsing Calendar Strings | covered | leading RRULE: stripped |
| `atomic::generated_rrule_parse_bad_frequency_err` | atomic | ## Error Semantics | covered | unknown frequency keyword is a parse error |
| `atomic::generated_rrule_parse_case_insensitive_canonical_display` | atomic | ## Parsing Calendar Strings | covered | lowercase shuffled input, canonical rendering |
| `atomic::generated_rrule_parse_unknown_property_err` | atomic | ## Error Semantics | covered | unknown property name is a parse error |
| `atomic::generated_set_display_rdate_exdate_lines` | atomic | ## Serialization | covered | single comma-joined RDATE/EXDATE lines; bare set |
| `atomic::generated_set_display_tzid_line` | atomic | ## Serialization | covered | TZID rendering of a zoned start |
| `atomic::generated_set_display_utc_shape` | atomic | ## Serialization | covered | DTSTART line + prefixed RRULE line |
| `atomic::generated_set_parse_bare_property_line` | atomic | ## Parsing Calendar Strings | covered | bare NAME=VALUE line treated as RRULE |
| `atomic::generated_set_parse_exrule_line_inert` | atomic | ## Parsing Calendar Strings | covered | EXRULE accepted, recorded nowhere, no effect |
| `atomic::generated_set_parse_missing_dtstart_err` | atomic | ## Error Semantics | covered | fragment without DTSTART is a parse error |
| `atomic::generated_set_parse_multiple_rrule_lines` | atomic | ## Parsing Calendar Strings | covered | multiple RRULE lines accumulate in order |
| `atomic::generated_set_parse_range_violation_parser_error` | atomic | ## Error Semantics | covered | BYMONTH=13 / BYWEEKNO=54 rejected at parse |
| `atomic::generated_set_parse_rdate_comma_list` | atomic | ## Parsing Calendar Strings | covered | comma-separated RDATE values |
| `atomic::generated_set_parse_tzid_dtstart` | atomic | ## Parsing Calendar Strings | covered | TZID parameter carries the zone |
| `atomic::generated_set_parse_utc_dtstart_stream` | atomic | ## Parsing Calendar Strings | covered | Z-suffixed DTSTART, stream in UTC |
| `atomic::generated_time_range_validation` | atomic | ## Validation Rules | covered | hour/minute/second ranges; boundary accepted |
| `atomic::generated_tz_constants_and_name` | atomic | ## Timezone and Daylight-Saving Behavior | covered | UTC and named constants report IANA names |
| `atomic::generated_tz_from_chrono_tz` | atomic | ## Timezone and Daylight-Saving Behavior | covered | From conversion from the zone-database type |
| `atomic::generated_until_before_start_err` | atomic | ## Validation Rules | covered | until earlier than start rejected + ok sibling |
| `atomic::generated_until_display_z` | atomic | ## Serialization | covered | UNTIL rendered wall-clock + Z |
| `atomic::generated_until_inclusive_boundary` | atomic | ## Occurrence Iteration | covered | occurrence equal to until is emitted |
| `atomic::generated_until_zone_rules` | atomic | ## Validation Rules | covered | until must be UTC when the start is zoned |
| `atomic::generated_unvalidated_display_preserves_raw` | atomic | ## Serialization | covered | raw rendering keeps negatives, drops explicit defaults |
| `atomic::generated_validate_normalizes_properties` | atomic | ## Normalization and Derived Properties | covered | validate fills time-of-day lists from the start |
| `atomic::generated_validated_display_property_order` | atomic | ## Serialization | covered | canonical part order with fills |
| `atomic::generated_weekly_fill_byday` | atomic | ## Normalization and Derived Properties | covered | BYDAY filled with the start weekday |
| `atomic::generated_window_inclusive_edges` | atomic | ## Occurrence Iteration | covered | after/before include edge instants |
| `atomic::generated_yearday_weekno_zero_err` | atomic | ## Validation Rules | covered | zero rejected for yearday/weekno via builder |
| `atomic::generated_yearly_fill_month_and_day` | atomic | ## Normalization and Derived Properties | covered | BYMONTH+BYMONTHDAY filled |
| `integration::errors_validation::generated_combination_error_after_parse` | integration | ## Error Semantics | covered | in-range combo fails validation post-parse |
| `integration::errors_validation::generated_error_values_display` | integration | ## Error Semantics | covered | both domains display through the shared type |
| `integration::errors_validation::generated_missing_dtstart_vs_bad_zone` | integration | ## Error Semantics | covered | missing DTSTART and unknown TZID classified |
| `integration::errors_validation::generated_range_error_domain_split` | integration | ## Error Semantics | covered | same violation: parse error vs validation error |
| `integration::errors_validation::generated_secondly_companion_vs_filled_frequencies` | integration | ## Validation Rules | covered | companion rule reachable only at SECONDLY |
| `integration::errors_validation::generated_until_zone_and_order_errors` | integration | ## Validation Rules | covered | zone + ordering rejections with ok sibling |
| `integration::round_trip::generated_builder_equals_parser` | integration | ## Cross-View Invariants | covered | CVI 2: builder and parser converge |
| `integration::round_trip::generated_display_fixed_point` | integration | ## Serialization | covered | canonical rendering is a fixed point |
| `integration::round_trip::generated_getter_display_agreement` | integration | ## Cross-View Invariants | covered | CVI 3: getters and text agree on non-defaults |
| `integration::round_trip::generated_multi_rule_set_roundtrip` | integration | ## Serialization | covered | two RRULE lines survive rendering |
| `integration::round_trip::generated_parse_display_reparse_stream_identical` | integration | ## Cross-View Invariants | covered | CVI 1: render/reparse keeps start, props, stream |
| `integration::round_trip::generated_rdate_exdate_roundtrip_stream` | integration | ## Cross-View Invariants | covered | CVI 1: rdate/exdate survive the round trip |
| `integration::round_trip::generated_validated_display_gains_fills_roundtrip` | integration | ## Cross-View Invariants | covered | CVI 4: fills visible in text, stream preserved |
| `integration::selection::generated_bysetpos_picks_within_day` | integration | ## Occurrence Iteration | covered | position filter over the BYHOUR cross product |
| `integration::selection::generated_byweekno_first_week_monday` | integration | ## Occurrence Iteration | covered | ISO week 1 Monday across two years |
| `integration::selection::generated_impossible_days_skipped` | integration | ## Occurrence Iteration | covered | day-31 months only; Feb 29 leap years only |
| `integration::selection::generated_last_business_day` | integration | ## Occurrence Iteration | covered | BYSETPOS=-1 over MO-FR vs recomputed last weekday |
| `integration::selection::generated_negative_yearday_selection` | integration | ## Occurrence Iteration | covered | -1 and 100 across a leap boundary |
| `integration::selection::generated_second_tuesday_and_last_sunday` | integration | ## Occurrence Iteration | covered | 2TU/-1SU verified by weekday+day properties |
| `integration::selection::generated_wkst_biweekly_divergence` | integration | ## Occurrence Iteration | covered | WKST alone changes a biweekly stream |
| `integration::streams::generated_cap_accounting_matrix` | integration | ## Cross-View Invariants | covered | CVI 5: len=min(n,m), limited iff m<=n |
| `integration::streams::generated_count_budget_before_exclusion` | integration | ## Occurrence Iteration | covered | count consumed before exclusions; until sibling |
| `integration::streams::generated_exdate_cuts_across_sources` | integration | ## Occurrence Iteration | covered | one exclusion removes rule hit and rdate |
| `integration::streams::generated_rdate_merge_ordering` | integration | ## Occurrence Iteration | covered | pre-start rdate first; duplicate kept |
| `integration::streams::generated_set_from_string_appends` | integration | ## Parsing Calendar Strings | covered | fragment merge appends; DTSTART replaces start |
| `integration::streams::generated_union_sorted_duplicates` | integration | ## Occurrence Iteration | covered | two-rule union sorted with duplicates |
| `integration::streams::generated_window_equals_filtered_stream` | integration | ## Cross-View Invariants | covered | CVI 6: window equals manual inclusive filter |
| `integration::zones::generated_fall_back_offsets` | integration | ## Timezone and Daylight-Saving Behavior | covered | offset sequence -0500,-0500,-0600 |
| `integration::zones::generated_hourly_gap_duplicate` | integration | ## Timezone and Daylight-Saving Behavior | covered | gap shift collides with the next hourly slot |
| `integration::zones::generated_spring_forward_daily_deltas` | integration | ## Timezone and Daylight-Saving Behavior | covered | 24/23/24h real deltas, wall clock held |
| `integration::zones::generated_utc_until_on_named_zone` | integration | ## Timezone and Daylight-Saving Behavior | covered | UTC until cuts a New York stream inclusively |
| `integration::zones::generated_window_edges_cross_zone` | integration | ## Timezone and Daylight-Saving Behavior | covered | window edges compare by instant across zones |
| `integration::zones::generated_zone_of_yield_by_source` | integration | ## Timezone and Daylight-Saving Behavior | covered | Tokyo rule + UTC rdate + Denver exclusion by instant |

Total: 97 | kept (covered): 97 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 97

Layer counts: atomic 64, integration 33.
