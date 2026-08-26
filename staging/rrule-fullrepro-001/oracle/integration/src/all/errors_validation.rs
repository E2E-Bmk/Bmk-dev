// Error-domain classification across the parser and builder surfaces, with
// positive siblings proving the corrected inputs work.
mod errors_validation {
    use super::*;

    #[test]
    fn generated_range_error_domain_split() {
        // Same violation, two domains: parsed text fails in the parser,
        // builder values fail in validation.
        let e = "DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;BYHOUR=25"
            .parse::<RRuleSet>()
            .unwrap_err();
        assert!(matches!(e, RRuleError::ParserError(_)));
        let dt = utc(2026, 2, 1, 8, 0, 0);
        let e = RRule::new(Frequency::Daily).by_hour(vec![25]).validate(dt).unwrap_err();
        assert!(matches!(e, RRuleError::ValidationError(_)));
        // Positive sibling: the in-range hour works identically both ways.
        let parsed = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;BYHOUR=5;COUNT=2").all(10);
        let built = RRule::new(Frequency::Daily)
            .by_hour(vec![5])
            .count(2)
            .build(dt)
            .unwrap()
            .all(10);
        assert_eq!(parsed.dates, built.dates);
        assert_eq!(parsed.dates, vec![utc(2026, 2, 2, 5, 0, 0), utc(2026, 2, 3, 5, 0, 0)]);
    }

    #[test]
    fn generated_combination_error_after_parse() {
        // In-range values with a forbidden frequency combination pass the
        // parser and fail validation.
        let e = "DTSTART:20260201T080000Z\nRRULE:FREQ=WEEKLY;BYMONTHDAY=10"
            .parse::<RRuleSet>()
            .unwrap_err();
        assert!(matches!(e, RRuleError::ValidationError(_)));
        // The same property under MONTHLY parses, validates, and iterates.
        let ok = pset("DTSTART:20260201T080000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=10;COUNT=2");
        assert_eq!(
            ok.all(10).dates,
            vec![utc(2026, 2, 10, 8, 0, 0), utc(2026, 3, 10, 8, 0, 0)]
        );
    }

    #[test]
    fn generated_until_zone_and_order_errors() {
        let dt = zdt(Tz::America__New_York, 2026, 2, 1, 9, 0, 0);
        // Zoned non-UTC until: rejected.
        let e = RRule::new(Frequency::Daily)
            .until(zdt(Tz::America__New_York, 2026, 2, 5, 9, 0, 0))
            .validate(dt)
            .unwrap_err();
        assert!(matches!(e, RRuleError::ValidationError(_)));
        // UTC until before the start: rejected.
        let e = RRule::new(Frequency::Daily)
            .until(utc(2026, 1, 1, 0, 0, 0))
            .validate(dt)
            .unwrap_err();
        assert!(matches!(e, RRuleError::ValidationError(_)));
        // UTC until after the start: the stream is cut inclusively.
        let set = RRule::new(Frequency::Daily)
            .until(utc(2026, 2, 3, 14, 0, 0)) // == 09:00 New York
            .build(dt)
            .unwrap();
        assert_eq!(
            set.all(10).dates,
            vec![
                zdt(Tz::America__New_York, 2026, 2, 1, 9, 0, 0),
                zdt(Tz::America__New_York, 2026, 2, 2, 9, 0, 0),
                zdt(Tz::America__New_York, 2026, 2, 3, 9, 0, 0),
            ]
        );
    }

    #[test]
    fn generated_missing_dtstart_vs_bad_zone() {
        let e = "RRULE:FREQ=DAILY".parse::<RRuleSet>().unwrap_err();
        assert!(matches!(e, RRuleError::ParserError(_)));
        let e = "DTSTART;TZID=Middle/Nowhere:20260201T080000\nRRULE:FREQ=DAILY"
            .parse::<RRuleSet>()
            .unwrap_err();
        assert!(matches!(e, RRuleError::ParserError(_)));
        // A recognized zone parses and yields zone-carrying occurrences.
        let ok = pset("DTSTART;TZID=Europe/Paris:20260201T080000\nRRULE:FREQ=DAILY;COUNT=1");
        assert_eq!(ok.all(5).dates, vec![zdt(Tz::Europe__Paris, 2026, 2, 1, 8, 0, 0)]);
    }

    #[test]
    fn generated_error_values_display() {
        // Errors are ordinary displayable values in both domains; the
        // classification survives the shared error type.
        let parse_err = RRule::<Unvalidated>::from_str("FREQ=NEVER").unwrap_err();
        assert!(matches!(parse_err, RRuleError::ParserError(_)));
        assert!(!parse_err.to_string().is_empty());
        let val_err = RRule::new(Frequency::Weekly)
            .by_month_day(vec![10])
            .validate(utc(2026, 2, 1, 8, 0, 0))
            .unwrap_err();
        assert!(matches!(val_err, RRuleError::ValidationError(_)));
        assert!(!val_err.to_string().is_empty());
    }

    #[test]
    fn generated_secondly_companion_vs_filled_frequencies() {
        // The companion rule interacts with the fills: every frequency except
        // SECONDLY gets a time-level fill, so a lone BYSETPOS validates there.
        let dt = utc(2026, 2, 1, 8, 0, 0);
        assert!(RRule::new(Frequency::Hourly).by_set_pos(vec![1]).validate(dt).is_ok());
        assert!(RRule::new(Frequency::Daily).by_set_pos(vec![1]).validate(dt).is_ok());
        let e = RRule::new(Frequency::Secondly).by_set_pos(vec![1]).validate(dt).unwrap_err();
        assert!(matches!(e, RRuleError::ValidationError(_)));
        // With an explicit BY part, positions select within each period.
        let ok = RRule::new(Frequency::Minutely)
            .by_second(vec![10, 40])
            .by_set_pos(vec![-1])
            .count(2)
            .build(utc(2026, 2, 1, 8, 0, 0))
            .unwrap();
        assert_eq!(
            ok.all(10).dates,
            vec![utc(2026, 2, 1, 8, 0, 40), utc(2026, 2, 1, 8, 1, 40)]
        );
    }
}
