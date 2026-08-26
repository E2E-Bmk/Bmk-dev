// Oracle atomic tests for the calendar recurrence engine
#![cfg(test)]
#![allow(clippy::all)]

use std::str::FromStr;

use chrono::{Datelike, Month, TimeZone, Timelike};
use rrule::{Frequency, NWeekday, RRule, RRuleError, RRuleResult, RRuleSet, Tz, Unvalidated, Weekday};

fn utc(y: i32, mo: u32, d: u32, h: u32, mi: u32, s: u32) -> chrono::DateTime<Tz> {
    Tz::UTC.with_ymd_and_hms(y, mo, d, h, mi, s).unwrap()
}

fn zdt(tz: Tz, y: i32, mo: u32, d: u32, h: u32, mi: u32, s: u32) -> chrono::DateTime<Tz> {
    tz.with_ymd_and_hms(y, mo, d, h, mi, s).unwrap()
}

fn pset(s: &str) -> RRuleSet {
    s.parse().unwrap()
}

// ---------------------------------------------------------------------------
// Vocabulary: Frequency, NWeekday
// ---------------------------------------------------------------------------

#[test]
fn generated_frequency_display_uppercase() {
    assert_eq!(Frequency::Yearly.to_string(), "YEARLY");
    assert_eq!(Frequency::Monthly.to_string(), "MONTHLY");
    assert_eq!(Frequency::Weekly.to_string(), "WEEKLY");
    assert_eq!(Frequency::Daily.to_string(), "DAILY");
    assert_eq!(Frequency::Hourly.to_string(), "HOURLY");
    assert_eq!(Frequency::Minutely.to_string(), "MINUTELY");
    assert_eq!(Frequency::Secondly.to_string(), "SECONDLY");
}

#[test]
fn generated_frequency_from_str_case_insensitive() {
    assert_eq!(Frequency::from_str("weekly").unwrap(), Frequency::Weekly);
    assert_eq!(Frequency::from_str("Secondly").unwrap(), Frequency::Secondly);
    assert_eq!(Frequency::from_str("DAILY").unwrap(), Frequency::Daily);
    assert!(Frequency::from_str("FORTNIGHTLY").is_err());
}

#[test]
fn generated_nweekday_constructor_forms() {
    assert_eq!(NWeekday::new(None, Weekday::Mon), NWeekday::Every(Weekday::Mon));
    assert_eq!(NWeekday::new(Some(2), Weekday::Tue), NWeekday::Nth(2, Weekday::Tue));
    assert_eq!(NWeekday::new(Some(-1), Weekday::Sun), NWeekday::Nth(-1, Weekday::Sun));
}

#[test]
fn generated_nweekday_display_notation() {
    assert_eq!(NWeekday::Every(Weekday::Mon).to_string(), "MO");
    assert_eq!(NWeekday::Nth(2, Weekday::Tue).to_string(), "2TU");
    assert_eq!(NWeekday::Nth(-1, Weekday::Sun).to_string(), "-1SU");
}

#[test]
fn generated_nweekday_from_str() {
    assert_eq!(NWeekday::from_str("-1SU").unwrap(), NWeekday::Nth(-1, Weekday::Sun));
    assert_eq!(NWeekday::from_str("FR").unwrap(), NWeekday::Every(Weekday::Fri));
    assert!(NWeekday::from_str("QQ").is_err());
}

// ---------------------------------------------------------------------------
// Rule builder: defaults, setters, getters, validate, build
// ---------------------------------------------------------------------------

#[test]
fn generated_builder_defaults() {
    let r = RRule::new(Frequency::Weekly);
    assert_eq!(r.get_freq(), Frequency::Weekly);
    assert_eq!(r.get_interval(), 1);
    assert_eq!(r.get_week_start(), Weekday::Mon);
    assert!(r.get_count().is_none());
    assert!(r.get_until().is_none());
    assert!(r.get_by_hour().is_empty());
    assert!(r.get_by_weekday().is_empty());
    assert!(r.get_by_month_day().is_empty());
}

#[test]
fn generated_by_month_setter_reports_numbers() {
    let r = RRule::new(Frequency::Yearly).by_month(&[Month::June, Month::July]);
    assert_eq!(r.get_by_month(), &[6, 7]);
}

#[test]
fn generated_builder_getters_after_set() {
    let until = utc(2027, 6, 1, 0, 0, 0);
    let r = RRule::new(Frequency::Daily)
        .interval(4)
        .count(9)
        .until(until)
        .week_start(Weekday::Wed);
    assert_eq!(r.get_interval(), 4);
    assert_eq!(r.get_count(), Some(9));
    assert_eq!(r.get_until(), Some(&until));
    assert_eq!(r.get_week_start(), Weekday::Wed);
}

#[test]
fn generated_validate_normalizes_properties() {
    let dt = utc(2026, 4, 15, 10, 30, 0);
    let rule = RRule::new(Frequency::Daily).count(2).validate(dt).unwrap();
    // Time-of-day lists are filled from the start instant during validation.
    assert_eq!(rule.get_by_hour(), &[10]);
    assert_eq!(rule.get_by_minute(), &[30]);
    assert_eq!(rule.get_by_second(), &[0]);
    assert_eq!(rule.get_freq(), Frequency::Daily);
}

#[test]
fn generated_build_wraps_single_rule_set() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRule::new(Frequency::Daily).count(2).build(dt).unwrap();
    assert_eq!(set.get_rrule().len(), 1);
    assert_eq!(*set.get_dt_start(), dt);
    let res = set.all(10);
    assert_eq!(res.dates, vec![dt, utc(2026, 2, 2, 8, 0, 0)]);
    // build propagates validation failures
    let bad = RRule::new(Frequency::Weekly).by_month_day(vec![10]).build(dt);
    assert!(matches!(bad, Err(RRuleError::ValidationError(_))));
}

// ---------------------------------------------------------------------------
// Single-rule string parsing
// ---------------------------------------------------------------------------

#[test]
fn generated_rrule_parse_case_insensitive_canonical_display() {
    let r: RRule<Unvalidated> = "interval=3;freq=daily;count=40".parse().unwrap();
    assert_eq!(r.to_string(), "FREQ=DAILY;COUNT=40;INTERVAL=3");
    assert_eq!(r.get_freq(), Frequency::Daily);
    assert_eq!(r.get_interval(), 3);
    assert_eq!(r.get_count(), Some(40));
}

#[test]
fn generated_rrule_parse_accepts_prefix() {
    let r: RRule<Unvalidated> = "RRULE:FREQ=WEEKLY;BYDAY=TU,-1SU;WKST=SU".parse().unwrap();
    assert_eq!(r.to_string(), "FREQ=WEEKLY;WKST=SU;BYDAY=TU,-1SU");
    assert_eq!(
        r.get_by_weekday(),
        &[NWeekday::Every(Weekday::Tue), NWeekday::Nth(-1, Weekday::Sun)]
    );
}

#[test]
fn generated_rrule_parse_unknown_property_err() {
    let e = RRule::<Unvalidated>::from_str("FREQ=DAILY;GLITTER=1").unwrap_err();
    assert!(matches!(e, RRuleError::ParserError(_)));
}

#[test]
fn generated_rrule_parse_bad_frequency_err() {
    let e = RRule::<Unvalidated>::from_str("FREQ=SOMETIMES").unwrap_err();
    assert!(matches!(e, RRuleError::ParserError(_)));
}

#[test]
fn generated_unvalidated_display_preserves_raw() {
    // Negative month days stay visible on an unvalidated rule.
    let r: RRule<Unvalidated> = "FREQ=MONTHLY;BYMONTHDAY=-1,10".parse().unwrap();
    assert_eq!(r.to_string(), "FREQ=MONTHLY;BYMONTHDAY=-1,10");
    // Explicit defaults are omitted from the rendering.
    let r: RRule<Unvalidated> = "FREQ=WEEKLY;INTERVAL=1;WKST=MO".parse().unwrap();
    assert_eq!(r.to_string(), "FREQ=WEEKLY");
}

// ---------------------------------------------------------------------------
// Calendar fragment parsing
// ---------------------------------------------------------------------------

#[test]
fn generated_set_parse_utc_dtstart_stream() {
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=3");
    assert_eq!(*set.get_dt_start(), utc(2026, 2, 1, 8, 0, 0));
    let res = set.all(10);
    assert_eq!(
        res.dates,
        vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 2, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
    );
    assert!(!res.limited);
}

#[test]
fn generated_set_parse_tzid_dtstart() {
    let set = pset("DTSTART;TZID=America/New_York:20261102T091500\nRRULE:FREQ=DAILY;COUNT=1");
    let start = *set.get_dt_start();
    assert_eq!(start.timezone().name(), "America/New_York");
    assert_eq!((start.hour(), start.minute()), (9, 15));
    assert_eq!(start, zdt(Tz::America__New_York, 2026, 11, 2, 9, 15, 0));
}

#[test]
fn generated_set_parse_missing_dtstart_err() {
    let e = "RRULE:FREQ=DAILY;COUNT=2".parse::<RRuleSet>().unwrap_err();
    assert!(matches!(e, RRuleError::ParserError(_)));
}

#[test]
fn generated_set_parse_bare_property_line() {
    let set = pset("DTSTART:20260201T080000Z\nFREQ=DAILY;COUNT=2");
    assert_eq!(set.get_rrule().len(), 1);
    assert_eq!(set.all(10).dates.len(), 2);
}

#[test]
fn generated_set_parse_multiple_rrule_lines() {
    let set = pset("DTSTART:20260101T090000Z\nRRULE:FREQ=DAILY;COUNT=3\nRRULE:FREQ=DAILY;INTERVAL=2;COUNT=2");
    assert_eq!(set.get_rrule().len(), 2);
    assert_eq!(set.get_rrule()[0].get_interval(), 1);
    assert_eq!(set.get_rrule()[1].get_interval(), 2);
}

#[test]
fn generated_set_parse_rdate_comma_list() {
    let set = pset("DTSTART:20260201T080000Z\nRDATE:20260301T080000Z,20260302T080000Z");
    assert_eq!(set.get_rdate().len(), 2);
    assert_eq!(
        set.all(10).dates,
        vec![utc(2026, 3, 1, 8, 0, 0), utc(2026, 3, 2, 8, 0, 0)]
    );
}

#[test]
fn generated_set_parse_exrule_line_inert() {
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=3\nEXRULE:FREQ=DAILY;COUNT=1");
    assert!(set.get_exrule().is_empty());
    assert_eq!(set.all(10).dates.len(), 3);
}

#[test]
fn generated_set_parse_range_violation_parser_error() {
    let e = "DTSTART:20260201T080000Z\nRRULE:FREQ=YEARLY;BYMONTH=13"
        .parse::<RRuleSet>()
        .unwrap_err();
    assert!(matches!(e, RRuleError::ParserError(_)));
    let e = "DTSTART:20260201T080000Z\nRRULE:FREQ=YEARLY;BYWEEKNO=54"
        .parse::<RRuleSet>()
        .unwrap_err();
    assert!(matches!(e, RRuleError::ParserError(_)));
}

// ---------------------------------------------------------------------------
// Normalization and derived properties
// ---------------------------------------------------------------------------

#[test]
fn generated_monthly_fill_from_start() {
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=MONTHLY;COUNT=2");
    let r = &set.get_rrule()[0];
    assert_eq!(r.get_by_month_day(), &[15]);
    assert_eq!(r.get_by_hour(), &[10]);
    assert_eq!(r.get_by_minute(), &[30]);
    assert_eq!(r.get_by_second(), &[0]);
}

#[test]
fn generated_weekly_fill_byday() {
    // 2026-04-15 is a Wednesday.
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=WEEKLY;COUNT=2");
    let r = &set.get_rrule()[0];
    assert_eq!(r.get_by_weekday(), &[NWeekday::Every(Weekday::Wed)]);
    assert!(r.get_by_month_day().is_empty());
}

#[test]
fn generated_yearly_fill_month_and_day() {
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=YEARLY;COUNT=2");
    let r = &set.get_rrule()[0];
    assert_eq!(r.get_by_month(), &[4]);
    assert_eq!(r.get_by_month_day(), &[15]);
}

#[test]
fn generated_no_date_fill_with_byday_present() {
    // A date-level selector suppresses the frequency fill entirely.
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=YEARLY;BYDAY=FR;COUNT=2");
    let r = &set.get_rrule()[0];
    assert!(r.get_by_month().is_empty());
    assert!(r.get_by_month_day().is_empty());
    assert_eq!(r.get_by_weekday(), &[NWeekday::Every(Weekday::Fri)]);
    // The time-level fill still applies.
    assert_eq!(r.get_by_hour(), &[10]);
}

#[test]
fn generated_monthday_zero_pruned() {
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=0;COUNT=2");
    let r = &set.get_rrule()[0];
    // Zero is discarded; the list is then empty, so the monthly fill applies.
    assert_eq!(r.get_by_month_day(), &[15]);
    assert_eq!(
        set.all(5).dates,
        vec![utc(2026, 4, 15, 10, 30, 0), utc(2026, 5, 15, 10, 30, 0)]
    );
}

#[test]
fn generated_negative_monthday_hidden_but_active() {
    let set = pset("DTSTART:20260101T090000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=-1;COUNT=3");
    let r = &set.get_rrule()[0];
    assert!(r.get_by_month_day().is_empty());
    assert!(!r.to_string().contains("BYMONTHDAY"));
    assert_eq!(
        set.all(5).dates,
        vec![utc(2026, 1, 31, 9, 0, 0), utc(2026, 2, 28, 9, 0, 0), utc(2026, 3, 31, 9, 0, 0)]
    );
}

#[test]
fn generated_lists_sorted_deduped() {
    let set = pset("DTSTART:20260101T000000Z\nRRULE:FREQ=DAILY;BYHOUR=9,9,6;BYMINUTE=30;BYSECOND=0;COUNT=4");
    let r = &set.get_rrule()[0];
    assert_eq!(r.get_by_hour(), &[6, 9]);
    assert!(r.to_string().contains("BYHOUR=6,9"));
    assert_eq!(
        set.all(10).dates,
        vec![
            utc(2026, 1, 1, 6, 30, 0),
            utc(2026, 1, 1, 9, 30, 0),
            utc(2026, 1, 2, 6, 30, 0),
            utc(2026, 1, 2, 9, 30, 0),
        ]
    );
}

// ---------------------------------------------------------------------------
// Validation rules
// ---------------------------------------------------------------------------

#[test]
fn generated_until_zone_rules() {
    let start_utc = utc(2026, 2, 1, 8, 0, 0);
    let start_ny = zdt(Tz::America__New_York, 2026, 2, 1, 8, 0, 0);
    let until_ny = zdt(Tz::America__New_York, 2026, 3, 1, 8, 0, 0);
    let until_utc = utc(2026, 3, 1, 8, 0, 0);
    // A zoned until that is not UTC is rejected, even in the start's own zone.
    assert!(RRule::new(Frequency::Daily).until(until_ny).validate(start_utc).is_err());
    assert!(RRule::new(Frequency::Daily).until(until_ny).validate(start_ny).is_err());
    // A UTC until is accepted for both start zones.
    assert!(RRule::new(Frequency::Daily).until(until_utc).validate(start_utc).is_ok());
    assert!(RRule::new(Frequency::Daily).until(until_utc).validate(start_ny).is_ok());
}

#[test]
fn generated_until_before_start_err() {
    let start = utc(2026, 2, 1, 8, 0, 0);
    let early = utc(2026, 1, 1, 8, 0, 0);
    let err = RRule::new(Frequency::Daily).until(early).validate(start).unwrap_err();
    assert!(matches!(err, RRuleError::ValidationError(_)));
    // Positive sibling: an until after the start validates and iterates.
    let ok = RRule::new(Frequency::Daily)
        .until(utc(2026, 2, 3, 8, 0, 0))
        .build(start)
        .unwrap();
    assert_eq!(ok.all(10).dates.len(), 3);
}

#[test]
fn generated_time_range_validation() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    assert!(matches!(
        RRule::new(Frequency::Daily).by_hour(vec![24]).validate(dt),
        Err(RRuleError::ValidationError(_))
    ));
    assert!(RRule::new(Frequency::Daily).by_minute(vec![60]).validate(dt).is_err());
    assert!(RRule::new(Frequency::Daily).by_second(vec![60]).validate(dt).is_err());
    // Boundary values are accepted.
    let ok = RRule::new(Frequency::Daily)
        .by_hour(vec![23])
        .by_minute(vec![59])
        .by_second(vec![59])
        .count(1)
        .build(dt)
        .unwrap();
    assert_eq!(ok.all(5).dates, vec![utc(2026, 2, 1, 23, 59, 59)]);
}

#[test]
fn generated_bymonthday_weekly_forbidden() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let err = RRule::new(Frequency::Weekly).by_month_day(vec![10]).validate(dt).unwrap_err();
    assert!(matches!(err, RRuleError::ValidationError(_)));
    // The same selector under a monthly frequency is valid and selects day 10.
    let ok = RRule::new(Frequency::Monthly).by_month_day(vec![10]).count(2).build(dt).unwrap();
    assert_eq!(ok.all(5).dates, vec![utc(2026, 2, 10, 8, 0, 0), utc(2026, 3, 10, 8, 0, 0)]);
}

#[test]
fn generated_byyearday_frequency_rules() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    for freq in [Frequency::Daily, Frequency::Weekly, Frequency::Monthly] {
        assert!(RRule::new(freq).by_year_day(vec![100]).validate(dt).is_err());
    }
    let ok = RRule::new(Frequency::Yearly).by_year_day(vec![100]).count(1).build(dt).unwrap();
    // Day 100 of 2026 is April 10.
    assert_eq!(ok.all(5).dates, vec![utc(2026, 4, 10, 8, 0, 0)]);
}

#[test]
fn generated_byweekno_yearly_only() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    assert!(RRule::new(Frequency::Monthly).by_week_no(vec![10]).validate(dt).is_err());
    assert!(RRule::new(Frequency::Weekly).by_week_no(vec![10]).validate(dt).is_err());
    assert!(RRule::new(Frequency::Yearly).by_week_no(vec![10]).validate(dt).is_ok());
}

#[test]
fn generated_bysetpos_range_and_zero() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    // Zero is rejected even with a companion selector.
    assert!(RRule::new(Frequency::Monthly)
        .by_set_pos(vec![0])
        .by_month_day(vec![5])
        .validate(dt)
        .is_err());
    // Monthly positions are bounded by +/-31.
    assert!(RRule::new(Frequency::Monthly)
        .by_set_pos(vec![32])
        .by_month_day(vec![5])
        .validate(dt)
        .is_err());
    assert!(RRule::new(Frequency::Monthly)
        .by_set_pos(vec![-31, 31])
        .by_month_day(vec![5])
        .validate(dt)
        .is_ok());
}

#[test]
fn generated_bysetpos_companion_secondly() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    // A secondly rule receives no fills, so a lone BYSETPOS has no companion.
    let err = RRule::new(Frequency::Secondly).by_set_pos(vec![2]).validate(dt).unwrap_err();
    assert!(matches!(err, RRuleError::ValidationError(_)));
    assert!(RRule::new(Frequency::Secondly)
        .by_set_pos(vec![2])
        .by_second(vec![10, 20])
        .validate(dt)
        .is_ok());
}

#[test]
fn generated_yearday_weekno_zero_err() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    assert!(RRule::new(Frequency::Yearly).by_year_day(vec![0]).validate(dt).is_err());
    assert!(RRule::new(Frequency::Yearly).by_week_no(vec![0]).validate(dt).is_err());
}

// ---------------------------------------------------------------------------
// Serialization
// ---------------------------------------------------------------------------

#[test]
fn generated_validated_display_property_order() {
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;INTERVAL=2;COUNT=2;WKST=SU");
    assert_eq!(
        set.get_rrule()[0].to_string(),
        "FREQ=DAILY;COUNT=2;INTERVAL=2;WKST=SU;BYHOUR=8;BYMINUTE=0;BYSECOND=0"
    );
}

#[test]
fn generated_until_display_z() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let rule = RRule::new(Frequency::Daily)
        .until(utc(2026, 3, 1, 8, 0, 0))
        .validate(dt)
        .unwrap();
    assert_eq!(rule.to_string(), "FREQ=DAILY;UNTIL=20260301T080000Z;BYHOUR=8;BYMINUTE=0;BYSECOND=0");
}

#[test]
fn generated_set_display_utc_shape() {
    let set = pset("DTSTART:20260415T103000Z\nRRULE:FREQ=MONTHLY;COUNT=2");
    assert_eq!(
        set.to_string(),
        "DTSTART:20260415T103000Z\nRRULE:FREQ=MONTHLY;COUNT=2;BYMONTHDAY=15;BYHOUR=10;BYMINUTE=30;BYSECOND=0"
    );
}

#[test]
fn generated_set_display_tzid_line() {
    let set = pset("DTSTART;TZID=Europe/Paris:20260201T080000\nRRULE:FREQ=DAILY;COUNT=3");
    let text = set.to_string();
    assert!(text.starts_with("DTSTART;TZID=Europe/Paris:20260201T080000\n"));
    assert!(text.contains("RRULE:FREQ=DAILY;COUNT=3"));
}

#[test]
fn generated_set_display_rdate_exdate_lines() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRuleSet::new(dt)
        .rdate(utc(2026, 3, 1, 8, 0, 0))
        .rdate(utc(2026, 3, 2, 8, 0, 0))
        .exdate(utc(2026, 3, 2, 8, 0, 0));
    assert_eq!(
        set.to_string(),
        "DTSTART:20260201T080000Z\nRDATE;VALUE=DATE-TIME:20260301T080000Z,20260302T080000Z\nEXDATE;VALUE=DATE-TIME:20260302T080000Z"
    );
    // A bare set renders only its DTSTART line.
    let empty = RRuleSet::new(dt);
    assert_eq!(empty.to_string(), "DTSTART:20260201T080000Z");
}

// ---------------------------------------------------------------------------
// Occurrence iteration
// ---------------------------------------------------------------------------

#[test]
fn generated_all_cap_and_limited_flag() {
    let res: RRuleResult = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY").all(4);
    assert_eq!(res.dates.len(), 4);
    assert!(res.limited);

    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=3").all(100);
    assert_eq!(res.dates.len(), 3);
    assert!(!res.limited);

    // Hitting the cap exactly still reports a limited collection.
    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=3").all(3);
    assert_eq!(res.dates.len(), 3);
    assert!(res.limited);
}

#[test]
fn generated_count_zero_empty() {
    let res = pset("DTSTART:20260101T090000Z\nRRULE:FREQ=DAILY;COUNT=0").all(10);
    assert!(res.dates.is_empty());
    assert!(!res.limited);
}

#[test]
fn generated_dtstart_emitted_iff_matching() {
    // Aligned start: the start instant is the first occurrence.
    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=2").all(10);
    assert_eq!(res.dates[0], utc(2026, 2, 1, 8, 0, 0));
    // Misaligned start: generation begins at the first matching instant.
    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;BYHOUR=14;COUNT=2").all(10);
    assert_eq!(res.dates, vec![utc(2026, 2, 1, 14, 0, 0), utc(2026, 2, 2, 14, 0, 0)]);
}

#[test]
fn generated_until_inclusive_boundary() {
    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;UNTIL=20260203T080000Z").all(10);
    assert_eq!(
        res.dates,
        vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 2, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
    );
    assert!(!res.limited);
}

#[test]
fn generated_window_inclusive_edges() {
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=5");
    let res = set
        .after(utc(2026, 2, 2, 8, 0, 0))
        .before(utc(2026, 2, 4, 8, 0, 0))
        .all(100);
    assert_eq!(
        res.dates,
        vec![utc(2026, 2, 2, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0), utc(2026, 2, 4, 8, 0, 0)]
    );
}

#[test]
fn generated_into_iter_ignores_window() {
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=5");
    let first = set.after(utc(2026, 2, 3, 8, 0, 0)).into_iter().next().unwrap();
    assert_eq!(first, utc(2026, 2, 1, 8, 0, 0));
    // The iterator walks the unbounded merged stream.
    let set = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY");
    let taken: Vec<_> = set.into_iter().take(3).collect();
    assert_eq!(
        taken,
        vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 2, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
    );
}

#[test]
fn generated_all_unchecked_finite() {
    let dates = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=5").all_unchecked();
    assert_eq!(dates.len(), 5);
    assert_eq!(dates[4], utc(2026, 2, 5, 8, 0, 0));
}

#[test]
fn generated_interval_stepping() {
    let res = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;INTERVAL=2;COUNT=3").all(10);
    assert_eq!(
        res.dates,
        vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0), utc(2026, 2, 5, 8, 0, 0)]
    );
    // A secondly rule steps across a day boundary.
    let res = pset("DTSTART:20260101T235957Z\nRRULE:FREQ=SECONDLY;INTERVAL=2;COUNT=3").all(10);
    assert_eq!(
        res.dates,
        vec![utc(2026, 1, 1, 23, 59, 57), utc(2026, 1, 1, 23, 59, 59), utc(2026, 1, 2, 0, 0, 1)]
    );
}

// ---------------------------------------------------------------------------
// Set composition
// ---------------------------------------------------------------------------

#[test]
fn generated_empty_set_behavior() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRuleSet::new(dt);
    assert_eq!(*set.get_dt_start(), dt);
    assert!(set.get_rrule().is_empty());
    assert!(set.get_rdate().is_empty());
    assert!(set.get_exdate().is_empty());
    assert!(set.get_exrule().is_empty());
    let res = set.all(10);
    assert!(res.dates.is_empty());
    assert!(!res.limited);
}

#[test]
fn generated_rdates_only_sorted() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRuleSet::new(dt)
        .rdate(utc(2026, 6, 1, 12, 0, 0))
        .rdate(utc(2026, 4, 1, 12, 0, 0));
    assert_eq!(
        set.all(10).dates,
        vec![utc(2026, 4, 1, 12, 0, 0), utc(2026, 6, 1, 12, 0, 0)]
    );
}

#[test]
fn generated_rdate_duplicates_preserved() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRuleSet::new(dt)
        .rdate(utc(2026, 5, 5, 5, 0, 0))
        .rdate(utc(2026, 5, 5, 5, 0, 0));
    assert_eq!(set.all(10).dates, vec![utc(2026, 5, 5, 5, 0, 0), utc(2026, 5, 5, 5, 0, 0)]);
}

#[test]
fn generated_exdate_removes_every_instance() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let set = RRuleSet::new(dt)
        .rdate(utc(2026, 5, 5, 5, 0, 0))
        .rdate(utc(2026, 5, 5, 5, 0, 0))
        .exdate(utc(2026, 5, 5, 5, 0, 0));
    assert!(set.all(10).dates.is_empty());
}

#[test]
fn generated_exdate_instant_across_zones() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    // 2026-04-01 04:00 in New York is 08:00 UTC (EDT, UTC-4).
    let set = RRuleSet::new(dt)
        .rdate(utc(2026, 4, 1, 8, 0, 0))
        .exdate(zdt(Tz::America__New_York, 2026, 4, 1, 4, 0, 0));
    assert!(set.all(10).dates.is_empty());
}

#[test]
fn generated_bulk_setters_replace() {
    let dt = utc(2026, 2, 1, 8, 0, 0);
    let r1 = RRule::new(Frequency::Daily).count(1).validate(dt).unwrap();
    let r2 = RRule::new(Frequency::Daily).interval(3).count(2).validate(dt).unwrap();
    let set = RRuleSet::new(dt)
        .rrule(r1)
        .rdate(utc(2026, 9, 9, 9, 0, 0))
        .exdate(utc(2026, 2, 1, 8, 0, 0))
        .set_rrules(vec![r2])
        .set_rdates(vec![utc(2026, 8, 8, 8, 0, 0)])
        .set_exdates(vec![]);
    assert_eq!(set.get_rrule().len(), 1);
    assert_eq!(set.get_rrule()[0].get_interval(), 3);
    assert_eq!(set.get_rdate(), &vec![utc(2026, 8, 8, 8, 0, 0)]);
    assert!(set.get_exdate().is_empty());
    assert_eq!(
        set.all(10).dates,
        vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 4, 8, 0, 0), utc(2026, 8, 8, 8, 0, 0)]
    );
}

// ---------------------------------------------------------------------------
// Timezone type and zone of yields
// ---------------------------------------------------------------------------

#[test]
fn generated_tz_constants_and_name() {
    assert_eq!(Tz::UTC.name(), "UTC");
    assert_eq!(Tz::America__New_York.name(), "America/New_York");
    assert_eq!(Tz::Europe__Paris.name(), "Europe/Paris");
    assert!(!Tz::UTC.is_local());
}

#[test]
fn generated_tz_from_chrono_tz() {
    let tz: Tz = chrono_tz::Tz::Asia__Tokyo.into();
    assert_eq!(tz.name(), "Asia/Tokyo");
    let dt = tz.with_ymd_and_hms(2026, 2, 1, 9, 0, 0).unwrap();
    assert_eq!(dt, zdt(Tz::Asia__Tokyo, 2026, 2, 1, 9, 0, 0));
}

#[test]
fn generated_occurrence_zone_by_source() {
    let set = pset("DTSTART;TZID=Asia/Tokyo:20260201T090000\nRRULE:FREQ=DAILY;COUNT=1\nRDATE:20260301T000000Z");
    let dates = set.all(10).dates;
    assert_eq!(dates.len(), 2);
    // Rule occurrences carry the start's zone; extra dates keep their own.
    assert_eq!(dates[0].timezone().name(), "Asia/Tokyo");
    assert_eq!(dates[0], zdt(Tz::Asia__Tokyo, 2026, 2, 1, 9, 0, 0));
    assert_eq!(dates[1].timezone().name(), "UTC");
}

// ---------------------------------------------------------------------------
// Daylight-saving behavior
// ---------------------------------------------------------------------------

#[test]
fn generated_dst_wallclock_daily() {
    // 2026-03-08 is the US spring-forward date.
    let set = pset("DTSTART;TZID=America/New_York:20260307T090000\nRRULE:FREQ=DAILY;COUNT=3");
    let dates = set.all(10).dates;
    assert_eq!(dates.len(), 3);
    for d in &dates {
        assert_eq!((d.hour(), d.minute()), (9, 0));
        assert_eq!(d.timezone().name(), "America/New_York");
    }
    // The transition day is 23 real hours after its predecessor.
    let delta = dates[1].signed_duration_since(dates[0]);
    assert_eq!(delta.num_hours(), 23);
    let delta = dates[2].signed_duration_since(dates[1]);
    assert_eq!(delta.num_hours(), 24);
}

#[test]
fn generated_dst_gap_shift_daily() {
    // 02:30 does not exist on 2026-03-08 in New York; it shifts to 03:30.
    let set = pset("DTSTART;TZID=America/New_York:20260307T023000\nRRULE:FREQ=DAILY;COUNT=3");
    let dates = set.all(10).dates;
    assert_eq!((dates[0].day(), dates[0].hour(), dates[0].minute()), (7, 2, 30));
    assert_eq!((dates[1].day(), dates[1].hour(), dates[1].minute()), (8, 3, 30));
    assert_eq!((dates[2].day(), dates[2].hour(), dates[2].minute()), (9, 2, 30));
}

#[test]
fn generated_dst_ambiguous_earlier_offset() {
    // 01:30 exists twice on 2026-11-01 in Chicago; the earlier offset wins.
    let set = pset("DTSTART;TZID=America/Chicago:20261031T013000\nRRULE:FREQ=DAILY;COUNT=3");
    let offsets: Vec<String> = set.all(10).dates.iter().map(|d| d.format("%z").to_string()).collect();
    assert_eq!(offsets, vec!["-0500", "-0500", "-0600"]);
}