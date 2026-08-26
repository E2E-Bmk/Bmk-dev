// Round trips binding the parser, the serializer, the getters, and the
// occurrence stream to one recurrence description.
mod round_trip {
    use super::*;

    #[test]
    fn generated_parse_display_reparse_stream_identical() {
        let text = "DTSTART;TZID=Europe/Paris:20260601T140000\nRRULE:FREQ=DAILY;INTERVAL=3;COUNT=4";
        let rendered = pset(text).to_string();
        let first = pset(text).all(20);
        let second = pset(&rendered).all(20);
        assert_eq!(first.dates, second.dates);
        assert_eq!(first.limited, second.limited);
        let reparsed = pset(&rendered);
        assert_eq!(*reparsed.get_dt_start(), zdt(Tz::Europe__Paris, 2026, 6, 1, 14, 0, 0));
        assert_eq!(reparsed.get_rrule()[0].get_interval(), 3);
        assert_eq!(reparsed.get_rrule()[0].get_count(), Some(4));
    }

    #[test]
    fn generated_display_fixed_point() {
        // Messy input: lowercase, shuffled order, duplicate list values.
        let messy = "DTSTART:20260901T061500Z\nRRULE:count=5;byhour=9,6,9;freq=daily;interval=2";
        let once = pset(messy).to_string();
        let twice = pset(&once).to_string();
        assert_eq!(once, twice);
        assert_eq!(
            once,
            "DTSTART:20260901T061500Z\nRRULE:FREQ=DAILY;COUNT=5;INTERVAL=2;BYHOUR=6,9;BYMINUTE=15;BYSECOND=0"
        );
    }

    #[test]
    fn generated_builder_equals_parser() {
        let dt = utc(2026, 2, 3, 9, 0, 0);
        let built = RRule::new(Frequency::Weekly)
            .interval(2)
            .count(3)
            .week_start(Weekday::Sun)
            .by_weekday(vec![NWeekday::Every(Weekday::Sun)])
            .build(dt)
            .unwrap();
        let parsed = pset("DTSTART:20260203T090000Z\nRRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=3;WKST=SU;BYDAY=SU");
        assert_eq!(
            built.get_rrule()[0].to_string(),
            parsed.get_rrule()[0].to_string()
        );
        assert_eq!(built.get_rrule()[0].get_week_start(), Weekday::Sun);
        let b = built.all(10);
        let p = parsed.all(10);
        assert_eq!(b.dates, p.dates);
        assert_eq!(
            b.dates,
            vec![utc(2026, 2, 15, 9, 0, 0), utc(2026, 3, 1, 9, 0, 0), utc(2026, 3, 15, 9, 0, 0)]
        );
    }

    #[test]
    fn generated_validated_display_gains_fills_roundtrip() {
        // The raw property text names no BY parts; the validated rendering
        // exposes the fills, and re-parsing it reproduces the stream.
        let raw: RRule<Unvalidated> = "FREQ=MONTHLY;COUNT=2".parse().unwrap();
        assert_eq!(raw.to_string(), "FREQ=MONTHLY;COUNT=2");
        let dt = utc(2026, 4, 15, 10, 30, 0);
        let validated = RRule::new(Frequency::Monthly).count(2).validate(dt).unwrap();
        assert_eq!(
            validated.to_string(),
            "FREQ=MONTHLY;COUNT=2;BYMONTHDAY=15;BYHOUR=10;BYMINUTE=30;BYSECOND=0"
        );
        let via_text = pset(&format!("DTSTART:20260415T103000Z\nRRULE:{}", validated));
        assert_eq!(
            via_text.all(10).dates,
            vec![utc(2026, 4, 15, 10, 30, 0), utc(2026, 5, 15, 10, 30, 0)]
        );
    }

    #[test]
    fn generated_multi_rule_set_roundtrip() {
        let text = "DTSTART:20260101T090000Z\nRRULE:FREQ=DAILY;COUNT=3\nRRULE:FREQ=DAILY;INTERVAL=2;COUNT=2";
        let rendered = pset(text).to_string();
        // Two RRULE lines survive in rule order.
        assert_eq!(rendered.matches("RRULE:").count(), 2);
        let original = pset(text).all(20);
        let reparsed = pset(&rendered).all(20);
        assert_eq!(original.dates, reparsed.dates);
        // Duplicates where the rules coincide are preserved on both sides.
        assert_eq!(original.dates.len(), 5);
    }

    #[test]
    fn generated_rdate_exdate_roundtrip_stream() {
        let text = "DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=4\nRDATE:20260110T080000Z\nEXDATE:20260203T080000Z";
        let rendered = pset(text).to_string();
        assert!(rendered.contains("RDATE;VALUE=DATE-TIME:20260110T080000Z"));
        assert!(rendered.contains("EXDATE;VALUE=DATE-TIME:20260203T080000Z"));
        let expected = vec![
            utc(2026, 1, 10, 8, 0, 0),
            utc(2026, 2, 1, 8, 0, 0),
            utc(2026, 2, 2, 8, 0, 0),
            utc(2026, 2, 4, 8, 0, 0),
        ];
        assert_eq!(pset(text).all(20).dates, expected);
        assert_eq!(pset(&rendered).all(20).dates, expected);
    }

    #[test]
    fn generated_getter_display_agreement() {
        // Non-default properties appear in the text exactly as the getters
        // report them; defaults disappear.
        let set = pset("DTSTART:20260601T070000Z\nRRULE:FREQ=MONTHLY;INTERVAL=6;WKST=TU;BYMONTHDAY=4,18;COUNT=3");
        let rule = &set.get_rrule()[0];
        let text = rule.to_string();
        assert_eq!(rule.get_interval(), 6);
        assert!(text.contains("INTERVAL=6"));
        assert_eq!(rule.get_week_start(), Weekday::Tue);
        assert!(text.contains("WKST=TU"));
        assert_eq!(rule.get_by_month_day(), &[4, 18]);
        assert!(text.contains("BYMONTHDAY=4,18"));

        let plain = pset("DTSTART:20260601T070000Z\nRRULE:FREQ=DAILY;COUNT=1");
        let rule = &plain.get_rrule()[0];
        assert_eq!(rule.get_interval(), 1);
        assert_eq!(rule.get_week_start(), Weekday::Mon);
        let text = rule.to_string();
        assert!(!text.contains("INTERVAL"));
        assert!(!text.contains("WKST"));
    }
}
