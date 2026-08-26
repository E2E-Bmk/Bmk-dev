// API-gateway style direct-limiter flows: burst admission, wait-and-retry,
// batch reservations, multiple quotas on one shared clock.

#[test]
fn generated_steady_drip_admits_all() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    let mut conforming = 0;
    let mut denials = 0;
    for _ in 0..18 {
        clock.advance(ms(120));
        match lim.check() {
            Ok(()) => conforming += 1,
            Err(denial) => {
                denials += 1;
                // Honoring the advertised wait must always conform.
                clock.advance(denial.wait_time_from(clock.now()));
                assert_eq!(Ok(()), lim.check());
                conforming += 1;
            }
        }
    }
    assert_eq!(conforming, 18);
    assert!(denials > 0, "the drip must be fast enough to hit denials");
}

#[test]
fn generated_burst_recovery_window() {
    let clock = FakeRelativeClock::default();
    // t = 166_666_666ns (truncated)
    let quota = Quota::per_second(nonzero!(6u32));
    let lim = RateLimiter::direct_with_clock(quota, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    for expected in [5u32, 4, 3, 2, 1, 0] {
        assert_eq!(Ok(expected), lim.check().map(|s| s.remaining_burst_capacity()));
    }
    assert!(lim.check().is_err());

    // Two per-cell intervals regain exactly two cells.
    clock.advance(ns(333_333_332));
    assert_eq!(Ok(1), lim.check().map(|s| s.remaining_burst_capacity()));
    assert_eq!(Ok(0), lim.check().map(|s| s.remaining_burst_capacity()));
    assert!(lim.check().is_err());

    // A full replenish restores the exact fresh-limiter countdown.
    clock.advance(quota.burst_size_replenished_in());
    for expected in [5u32, 4, 3, 2, 1, 0] {
        assert_eq!(Ok(expected), lim.check().map(|s| s.remaining_burst_capacity()));
    }
    assert!(lim.check().is_err());
}

#[test]
fn generated_batch_reservation_pipeline() {
    let clock = FakeRelativeClock::default();
    // t = 166_666_666ns, tau = 5t
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(6u32)), clock.clone());
    assert!(lim.check_n(nonzero!(3u32)).unwrap().is_ok());
    assert!(lim.check_n(nonzero!(2u32)).unwrap().is_ok());

    // An impossible reservation reports capacity and leaves state untouched.
    assert_eq!(Err(InsufficientCapacity(6)), lim.check_n(nonzero!(7u32)));

    // The next feasible batch is denied right now but advertises its instant.
    let denial = lim.check_n(nonzero!(2u32)).unwrap().unwrap_err();
    assert_eq!(denial.earliest_possible(), Nanos::new(166_666_666));
    let wait = denial.wait_time_from(clock.now());
    assert_eq!(wait, ns(166_666_666));
    clock.advance(wait);
    assert!(lim.check_n(nonzero!(2u32)).unwrap().is_ok());

    // Everything is spent again at this instant.
    assert!(lim.check().is_err());
}

#[test]
fn generated_two_quotas_one_clock() {
    let clock = FakeRelativeClock::default();
    let quota_a = Quota::per_second(nonzero!(2u32)); // t = 500ms
    let quota_b = Quota::with_period(ms(300)).unwrap().allow_burst(nonzero!(2u32)); // t = 300ms
    let lim_a = RateLimiter::direct_with_clock(quota_a, clock.clone());
    let lim_b = RateLimiter::direct_with_clock(quota_b, clock.clone());

    for _ in 0..2 {
        assert_eq!(Ok(()), lim_a.check());
        assert_eq!(Ok(()), lim_b.check());
    }
    let denial_a = lim_a.check().unwrap_err();
    let denial_b = lim_b.check().unwrap_err();
    assert_eq!(denial_a.earliest_possible(), Nanos::new(500_000_000));
    assert_eq!(denial_b.earliest_possible(), Nanos::new(300_000_000));
    assert_eq!(denial_a.quota(), quota_a);
    assert_eq!(denial_b.quota(), quota_b);

    // The faster quota recovers first on the shared clock.
    clock.advance(ms(300));
    assert_eq!(Ok(()), lim_b.check());
    assert!(lim_a.check().is_err());
    clock.advance(ms(200));
    assert_eq!(Ok(()), lim_a.check());
}
