// BY-part selection engine checked against independently recomputed
// calendar properties.
mod selection {
    use super::*;

    #[test]
    fn generated_last_business_day() {
        let set = pset("DTSTART:20260501T170000Z\nRRULE:FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1;COUNT=4");
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 4);
        let months: Vec<u32> = dates.iter().map(|d| d.month()).collect();
        assert_eq!(months, vec![5, 6, 7, 8]);
        for d in &dates {
            // Recompute: the last weekday of that month.
            let last = days_in_month(d.year(), d.month());
            let mut probe = chrono::NaiveDate::from_ymd_opt(d.year(), d.month(), last).unwrap();
            while matches!(probe.weekday(), Weekday::Sat | Weekday::Sun) {
                probe = probe.pred_opt().unwrap();
            }
            assert_eq!(d.day(), probe.day());
            assert!(!matches!(d.weekday(), Weekday::Sat | Weekday::Sun));
            assert_eq!(d.hour(), 17);
        }
    }

    #[test]
    fn generated_second_tuesday_and_last_sunday() {
        let set = pset("DTSTART:20260301T080000Z\nRRULE:FREQ=MONTHLY;BYDAY=2TU,-1SU;COUNT=6");
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 6);
        // Two occurrences per month, March through May 2026.
        for pair in dates.chunks(2) {
            assert_eq!(pair[0].month(), pair[1].month());
        }
        for d in &dates {
            match d.weekday() {
                Weekday::Tue => {
                    // The second Tuesday has day in 8..=14.
                    assert!((8..=14).contains(&d.day()));
                }
                Weekday::Sun => {
                    // The last Sunday is within 7 days of the month end.
                    assert!(d.day() + 7 > days_in_month(d.year(), d.month()));
                }
                other => panic!("unexpected weekday {other}"),
            }
        }
    }

    #[test]
    fn generated_impossible_days_skipped() {
        // Day 31 exists in Jan/Mar/May/Jul only among the first months of 2026.
        let set = pset("DTSTART:20260131T080000Z\nRRULE:FREQ=MONTHLY;COUNT=4");
        assert_eq!(
            set.all(10).dates,
            vec![
                utc(2026, 1, 31, 8, 0, 0),
                utc(2026, 3, 31, 8, 0, 0),
                utc(2026, 5, 31, 8, 0, 0),
                utc(2026, 7, 31, 8, 0, 0),
            ]
        );
        // February 29 recurs only in leap years.
        let set = pset("DTSTART:20280229T120000Z\nRRULE:FREQ=YEARLY;COUNT=2");
        assert_eq!(
            set.all(10).dates,
            vec![utc(2028, 2, 29, 12, 0, 0), utc(2032, 2, 29, 12, 0, 0)]
        );
    }

    #[test]
    fn generated_negative_yearday_selection() {
        let set = pset("DTSTART:20260601T060000Z\nRRULE:FREQ=YEARLY;BYYEARDAY=-1,100;COUNT=4");
        assert_eq!(
            set.all(10).dates,
            vec![
                utc(2026, 12, 31, 6, 0, 0),
                utc(2027, 4, 10, 6, 0, 0),  // day 100 of 2027
                utc(2027, 12, 31, 6, 0, 0),
                utc(2028, 4, 9, 6, 0, 0),   // day 100 of leap-year 2028
            ]
        );
    }

    #[test]
    fn generated_byweekno_first_week_monday() {
        let set = pset("DTSTART:20261001T120000Z\nRRULE:FREQ=YEARLY;BYWEEKNO=1;BYDAY=MO;COUNT=2");
        assert_eq!(
            set.all(10).dates,
            vec![utc(2027, 1, 4, 12, 0, 0), utc(2028, 1, 3, 12, 0, 0)]
        );
    }

    #[test]
    fn generated_wkst_biweekly_divergence() {
        // Identical rules except WKST: the interval steps over different
        // week boundaries, so the streams diverge.
        let mo = pset("DTSTART:20260203T090000Z\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SU;WKST=MO;COUNT=2");
        let su = pset("DTSTART:20260203T090000Z\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SU;WKST=SU;COUNT=2");
        assert_eq!(
            mo.all(10).dates,
            vec![utc(2026, 2, 8, 9, 0, 0), utc(2026, 2, 22, 9, 0, 0)]
        );
        assert_eq!(
            su.all(10).dates,
            vec![utc(2026, 2, 15, 9, 0, 0), utc(2026, 3, 1, 9, 0, 0)]
        );
    }

    #[test]
    fn generated_bysetpos_picks_within_day() {
        // The daily candidate list is the BYHOUR cross product; BYSETPOS
        // keeps one instant per day from it.
        let first = pset("DTSTART:20260101T000000Z\nRRULE:FREQ=DAILY;BYHOUR=6,9;BYMINUTE=15;BYSECOND=0;BYSETPOS=1;COUNT=3");
        assert_eq!(
            first.all(10).dates,
            vec![utc(2026, 1, 1, 6, 15, 0), utc(2026, 1, 2, 6, 15, 0), utc(2026, 1, 3, 6, 15, 0)]
        );
        let last = pset("DTSTART:20260101T000000Z\nRRULE:FREQ=DAILY;BYHOUR=6,9;BYMINUTE=15;BYSECOND=0;BYSETPOS=-1;COUNT=3");
        assert_eq!(
            last.all(10).dates,
            vec![utc(2026, 1, 1, 9, 15, 0), utc(2026, 1, 2, 9, 15, 0), utc(2026, 1, 3, 9, 15, 0)]
        );
    }
}
