// Scheduling flows: retry schedules from denial instants on pre-advanced
// clocks, regain intervals matching quota introspection.

#[test]
fn generated_wait_and_retry_schedule() {
    let clock = FakeRelativeClock::default();
    clock.advance(Duration::from_secs(2));
    // t = 500ms, tau = 500ms; start reference is the 2s reading.
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    assert_eq!(Ok(()), lim.check());
    assert_eq!(Ok(()), lim.check());

    let first = lim.check().unwrap_err();
    assert_eq!(first.earliest_possible(), Nanos::new(2_500_000_000));
    assert_eq!(format!("{}", first), "rate-limited until Nanos(2.5s)");

    clock.advance(first.wait_time_from(clock.now()));
    assert_eq!(Ok(()), lim.check());

    let second = lim.check().unwrap_err();
    assert_eq!(second.earliest_possible(), Nanos::new(3_000_000_000));
    assert_eq!(format!("{}", second), "rate-limited until Nanos(3s)");

    clock.advance(second.wait_time_from(clock.now()));
    assert_eq!(Ok(()), lim.check());
}

#[test]
fn generated_quota_ladder_regain_intervals() {
    let clock = FakeRelativeClock::default();
    let per_minute = Quota::per_minute(nonzero!(30u32)); // t = 2s
    let single = Quota::with_period(ms(1500)).unwrap(); // burst 1
    assert_eq!(per_minute.replenish_interval(), Duration::from_secs(2));
    assert_eq!(single.replenish_interval(), ms(1500));

    let lim_a = RateLimiter::direct_with_clock(per_minute, clock.clone());
    let lim_b = RateLimiter::direct_with_clock(single, clock.clone());

    // Drain both budgets completely.
    assert!(lim_a.check_n(nonzero!(30u32)).unwrap().is_ok());
    assert_eq!(Ok(()), lim_b.check());
    assert!(lim_a.check().is_err());
    assert!(lim_b.check().is_err());

    // Probe in 500ms steps: each limiter regains exactly at its own interval.
    let mut a_regained_at = None;
    let mut b_regained_at = None;
    for step in 1..=6 {
        clock.advance(ms(500));
        if a_regained_at.is_none() && lim_a.check().is_ok() {
            a_regained_at = Some(step * 500);
        }
        if b_regained_at.is_none() && lim_b.check().is_ok() {
            b_regained_at = Some(step * 500);
        }
    }
    assert_eq!(a_regained_at, Some(2000));
    assert_eq!(b_regained_at, Some(1500));

    // The full-burst figure also matches observation: a fresh drain of the
    // per-minute quota conforms again after burst_size_replenished_in.
    clock.advance(Duration::from_secs(120)); // fully replenish first
    assert!(lim_a.check_n(nonzero!(30u32)).unwrap().is_ok());
    assert!(lim_a.check_n(nonzero!(30u32)).unwrap().is_err());
    clock.advance(per_minute.burst_size_replenished_in());
    assert!(lim_a.check_n(nonzero!(30u32)).unwrap().is_ok());
}
