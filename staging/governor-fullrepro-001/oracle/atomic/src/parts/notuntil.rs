// Denial interrogation: earliest instants, wait-time math and clamping,
// display sentences, quota round trips, pre-advanced start references.

#[test]
fn generated_denial_earliest_and_wait() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    assert_eq!(Ok(()), lim.check());
    let denial = lim.check().unwrap_err();
    assert_eq!(denial.earliest_possible(), Nanos::new(1_000_000_000));
    assert_eq!(denial.wait_time_from(clock.now()), Duration::from_secs(1));
    // From a later measurement point, the wait shrinks accordingly...
    assert_eq!(denial.wait_time_from(Nanos::new(400_000_000)), ms(600));
    // ...and clamps to zero at or past the earliest instant.
    assert_eq!(denial.wait_time_from(Nanos::new(1_000_000_000)), Duration::ZERO);
    assert_eq!(denial.wait_time_from(Nanos::new(1_500_000_000)), Duration::ZERO);
}

#[test]
fn generated_display_fixed_sentence() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    let _ = lim.check();
    let denial = lim.check().unwrap_err();
    assert_eq!(format!("{}", denial), "rate-limited until Nanos(1s)");
}

#[test]
fn generated_pre_advanced_start_reference() {
    let clock = FakeRelativeClock::default();
    clock.advance(Duration::from_secs(3));
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    assert_eq!(Ok(()), lim.check());
    let denial = lim.check().unwrap_err();
    // The start reference includes the pre-construction offset.
    assert_eq!(denial.earliest_possible(), Nanos::new(4_000_000_000));
    assert_eq!(format!("{}", denial), "rate-limited until Nanos(4s)");
    assert_eq!(denial.wait_time_from(clock.now()), Duration::from_secs(1));
}

#[test]
fn generated_wait_advance_reconform() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    for _ in 0..4 {
        assert_eq!(Ok(()), lim.check());
    }
    let denial = lim.check().unwrap_err();
    let wait = denial.wait_time_from(clock.now());
    // One nanosecond short of the advertised wait still denies;
    clock.advance(wait - ns(1));
    assert!(lim.check().is_err());
    // the full advertised wait conforms.
    clock.advance(ns(1));
    assert_eq!(Ok(()), lim.check());
}

#[test]
fn generated_quota_round_trip_on_denial() {
    let clock = FakeRelativeClock::default();
    let quota = Quota::with_period(ms(130)).unwrap().allow_burst(nonzero!(2u32));
    let lim = RateLimiter::direct_with_clock(quota, clock.clone());
    let _ = lim.check();
    let _ = lim.check();
    let denial = lim.check().unwrap_err();
    assert_eq!(denial.quota(), quota);
    assert_eq!(denial.quota().replenish_interval(), ms(130));
    assert_eq!(denial.quota().burst_size().get(), 2);
}

#[test]
fn generated_batch_denial_earliest() {
    let clock = FakeRelativeClock::default();
    // t = 250ms, tau = 750ms
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    assert_eq!(Ok(()), lim.check()); // TAT = 250ms
    let denial = lim.check_n(nonzero!(4u32)).unwrap().unwrap_err();
    // earliest = (TAT + 3t) - tau = 250ms
    assert_eq!(denial.earliest_possible(), Nanos::new(250_000_000));
    clock.advance(ms(250));
    assert!(lim.check_n(nonzero!(4u32)).unwrap().is_ok());
}
