// Set algebra: unions, extra dates, exclusions, windows, and cap accounting
// observed through the merged occurrence stream.
mod streams {
    use super::*;

    #[test]
    fn generated_union_sorted_duplicates() {
        let set = pset("DTSTART:20260101T090000Z\nRRULE:FREQ=DAILY;COUNT=3\nRRULE:FREQ=DAILY;INTERVAL=2;COUNT=2");
        assert_eq!(
            set.all(20).dates,
            vec![
                utc(2026, 1, 1, 9, 0, 0),
                utc(2026, 1, 1, 9, 0, 0),
                utc(2026, 1, 2, 9, 0, 0),
                utc(2026, 1, 3, 9, 0, 0),
                utc(2026, 1, 3, 9, 0, 0),
            ]
        );
    }

    #[test]
    fn generated_rdate_merge_ordering() {
        let dt = utc(2026, 2, 1, 8, 0, 0);
        let rule = RRule::new(Frequency::Daily).count(3).validate(dt).unwrap();
        let set = RRuleSet::new(dt)
            .rrule(rule)
            .rdate(utc(2026, 2, 2, 8, 0, 0)) // duplicates the rule's 2nd hit
            .rdate(utc(2026, 1, 15, 8, 0, 0)); // precedes the start
        assert_eq!(
            set.all(20).dates,
            vec![
                utc(2026, 1, 15, 8, 0, 0),
                utc(2026, 2, 1, 8, 0, 0),
                utc(2026, 2, 2, 8, 0, 0),
                utc(2026, 2, 2, 8, 0, 0),
                utc(2026, 2, 3, 8, 0, 0),
            ]
        );
    }

    #[test]
    fn generated_exdate_cuts_across_sources() {
        // One exclusion removes the rule occurrence AND the duplicate rdate.
        let dt = utc(2026, 2, 1, 8, 0, 0);
        let rule = RRule::new(Frequency::Daily).count(3).validate(dt).unwrap();
        let set = RRuleSet::new(dt)
            .rrule(rule)
            .rdate(utc(2026, 2, 2, 8, 0, 0))
            .exdate(utc(2026, 2, 2, 8, 0, 0));
        assert_eq!(
            set.all(20).dates,
            vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
        );
    }

    #[test]
    fn generated_count_budget_before_exclusion() {
        // COUNT is consumed by generation before exclusions apply: the
        // excluded occurrence is not replaced by a later one.
        let dt = utc(2026, 2, 1, 8, 0, 0);
        let rule = RRule::new(Frequency::Daily).count(3).validate(dt).unwrap();
        let set = RRuleSet::new(dt).rrule(rule).exdate(utc(2026, 2, 2, 8, 0, 0));
        assert_eq!(
            set.all(20).dates,
            vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
        );
        // The equivalent UNTIL-bounded rule behaves identically here.
        let rule = RRule::new(Frequency::Daily)
            .until(utc(2026, 2, 3, 8, 0, 0))
            .validate(dt)
            .unwrap();
        let set = RRuleSet::new(dt).rrule(rule).exdate(utc(2026, 2, 2, 8, 0, 0));
        assert_eq!(
            set.all(20).dates,
            vec![utc(2026, 2, 1, 8, 0, 0), utc(2026, 2, 3, 8, 0, 0)]
        );
    }

    #[test]
    fn generated_window_equals_filtered_stream() {
        let text = "DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=10";
        let lo = utc(2026, 2, 3, 8, 0, 0);
        let hi = utc(2026, 2, 7, 8, 0, 0);
        let windowed = pset(text).after(lo).before(hi).all(100).dates;
        let manual: Vec<_> = pset(text)
            .all(100)
            .dates
            .into_iter()
            .filter(|d| *d >= lo && *d <= hi)
            .collect();
        assert_eq!(windowed, manual);
        assert_eq!(windowed.len(), 5);
    }

    #[test]
    fn generated_cap_accounting_matrix() {
        let text = "DTSTART:20260201T080000Z\nRRULE:FREQ=DAILY;COUNT=5";
        let r = pset(text).all(3);
        assert_eq!(r.dates.len(), 3);
        assert!(r.limited);
        let r = pset(text).all(5);
        assert_eq!(r.dates.len(), 5);
        assert!(r.limited);
        let r = pset(text).all(6);
        assert_eq!(r.dates.len(), 5);
        assert!(!r.limited);
    }

    #[test]
    fn generated_set_from_string_appends() {
        // Without a DTSTART line the fragment appends to the existing set.
        let dt = utc(2026, 7, 1, 6, 0, 0);
        let rule = RRule::new(Frequency::Daily).count(2).validate(dt).unwrap();
        let set = RRuleSet::new(dt)
            .rrule(rule)
            .set_from_string("RRULE:FREQ=WEEKLY;COUNT=1")
            .unwrap();
        assert_eq!(set.get_rrule().len(), 2);
        assert_eq!(*set.get_dt_start(), dt);
        assert_eq!(
            set.all(20).dates,
            vec![
                utc(2026, 7, 1, 6, 0, 0),
                utc(2026, 7, 1, 6, 0, 0),
                utc(2026, 7, 2, 6, 0, 0),
            ]
        );
        // With a DTSTART line the fragment replaces the start.
        let rule = RRule::new(Frequency::Daily).count(1).validate(dt).unwrap();
        let set = RRuleSet::new(dt)
            .rrule(rule)
            .set_from_string("DTSTART:20261225T120000Z\nRDATE:20261226T120000Z")
            .unwrap();
        assert_eq!(*set.get_dt_start(), utc(2026, 12, 25, 12, 0, 0));
        assert_eq!(set.get_rdate(), &vec![utc(2026, 12, 26, 12, 0, 0)]);
    }
}
