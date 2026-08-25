// Timezone handling as a second projection of the same recurrence: zones of
// yielded instants, DST transitions, and instant-based comparisons.
mod zones {
    use super::*;

    #[test]
    fn generated_zone_of_yield_by_source() {
        // A Tokyo rule, a UTC extra date, and a Denver-expressed exclusion
        // that hits the Tokyo occurrence by instant.
        let dt = zdt(Tz::Asia__Tokyo, 2026, 2, 2, 9, 0, 0);
        let rule = RRule::new(Frequency::Daily).count(2).validate(dt).unwrap();
        let set = RRuleSet::new(dt)
            .rrule(rule)
            .rdate(utc(2026, 2, 5, 0, 0, 0))
            // 2026-02-03 09:00 Tokyo == 2026-02-02 17:00 Denver (UTC-7).
            .exdate(zdt(Tz::America__Denver, 2026, 2, 2, 17, 0, 0));
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 2);
        assert_eq!(dates[0].timezone().name(), "Asia/Tokyo");
        assert_eq!(dates[0], zdt(Tz::Asia__Tokyo, 2026, 2, 2, 9, 0, 0));
        assert_eq!(dates[1].timezone().name(), "UTC");
        assert_eq!(dates[1], utc(2026, 2, 5, 0, 0, 0));
    }

    #[test]
    fn generated_spring_forward_daily_deltas() {
        // Wall-clock 09:00 is held; real deltas are 24h, 23h, 24h around the
        // 2026-03-08 US transition.
        let set = pset("DTSTART;TZID=America/Denver:20260306T090000\nRRULE:FREQ=DAILY;COUNT=4");
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 4);
        for d in &dates {
            assert_eq!((d.hour(), d.minute()), (9, 0));
        }
        let deltas: Vec<i64> = dates
            .windows(2)
            .map(|w| w[1].signed_duration_since(w[0]).num_hours())
            .collect();
        assert_eq!(deltas, vec![24, 23, 24]);
    }

    #[test]
    fn generated_hourly_gap_duplicate() {
        // Hourly across the spring-forward gap: the 02:30 slot shifts onto
        // 03:30 and collides with the regular 03:30 occurrence.
        let set = pset("DTSTART;TZID=America/Denver:20260308T003000\nRRULE:FREQ=HOURLY;COUNT=5");
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 5);
        let locals: Vec<(u32, u32)> = dates.iter().map(|d| (d.hour(), d.minute())).collect();
        assert_eq!(locals, vec![(0, 30), (1, 30), (3, 30), (3, 30), (4, 30)]);
        // The two 03:30 entries are the same absolute instant.
        assert_eq!(dates[2], dates[3]);
    }

    #[test]
    fn generated_fall_back_offsets() {
        // Daily 01:30 across the Chicago fall-back: the ambiguous day picks
        // the earlier (daylight) offset; the next day is standard time.
        let set = pset("DTSTART;TZID=America/Chicago:20261031T013000\nRRULE:FREQ=DAILY;COUNT=3");
        let dates = set.all(10).dates;
        let view: Vec<(u32, String)> = dates
            .iter()
            .map(|d| (d.hour(), d.format("%z").to_string()))
            .collect();
        assert_eq!(
            view,
            vec![
                (1, "-0500".to_string()),
                (1, "-0500".to_string()),
                (1, "-0600".to_string()),
            ]
        );
        // Wall clock is stable even though the offsets change.
        for d in &dates {
            assert_eq!(d.minute(), 30);
        }
    }

    #[test]
    fn generated_utc_until_on_named_zone() {
        // A UTC UNTIL cuts a New York stream at the equivalent local time,
        // inclusively.
        let set = pset("DTSTART;TZID=America/New_York:20260201T090000\nRRULE:FREQ=DAILY;UNTIL=20260205T140000Z");
        let dates = set.all(10).dates;
        assert_eq!(dates.len(), 5);
        assert_eq!(dates[0], zdt(Tz::America__New_York, 2026, 2, 1, 9, 0, 0));
        assert_eq!(dates[4], zdt(Tz::America__New_York, 2026, 2, 5, 9, 0, 0));
        assert_eq!(dates[4].timezone().name(), "America/New_York");
    }

    #[test]
    fn generated_window_edges_cross_zone() {
        // Window edges compare by instant: an edge expressed in Denver
        // selects the same occurrences as the equivalent UTC edge.
        let text = "DTSTART:20260201T170000Z\nRRULE:FREQ=DAILY;COUNT=8";
        let denver_edge = zdt(Tz::America__Denver, 2026, 2, 3, 10, 0, 0); // == 17:00 UTC
        let utc_edge = utc(2026, 2, 3, 17, 0, 0);
        let via_denver = pset(text).after(denver_edge).all(100).dates;
        let via_utc = pset(text).after(utc_edge).all(100).dates;
        assert_eq!(via_denver, via_utc);
        assert_eq!(via_denver.len(), 6);
        assert_eq!(via_denver[0], utc(2026, 2, 3, 17, 0, 0));
    }
}
