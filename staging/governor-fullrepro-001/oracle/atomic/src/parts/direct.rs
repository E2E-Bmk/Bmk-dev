// Direct limiter decisions: burst admission, exact boundaries, single-cell
// regain, denial statelessness, batch rule, capacity failures.

#[test]
fn generated_fresh_limiter_admits_burst() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(6u32)), clock.clone());
    for _ in 0..6 {
        assert_eq!(Ok(()), lim.check());
    }
    assert!(lim.check().is_err());
}

#[test]
fn generated_single_cell_regain_exact_boundary() {
    let clock = FakeRelativeClock::default();
    // t = 250ms, tau = 750ms
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    for _ in 0..4 {
        assert_eq!(Ok(()), lim.check());
    }
    // One nanosecond before the boundary still denies...
    clock.advance(ns(249_999_999));
    assert!(lim.check().is_err());
    // ...and the exact boundary conforms.
    clock.advance(ns(1));
    assert_eq!(Ok(()), lim.check());
    // The regained cell is consumed: an immediate re-check denies again.
    assert!(lim.check().is_err());
}

#[test]
fn generated_no_extra_cell_after_long_idle() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    for _ in 0..4 {
        assert_eq!(Ok(()), lim.check());
    }
    assert!(lim.check().is_err());
    // Idling much longer than a full replenish must not mint an extra cell.
    clock.advance(Duration::from_secs(30));
    for _ in 0..4 {
        assert_eq!(Ok(()), lim.check());
    }
    assert!(lim.check().is_err());
}

#[test]
fn generated_denials_do_not_consume() {
    let clock = FakeRelativeClock::default();
    // t = 500ms, tau = 500ms
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    assert_eq!(Ok(()), lim.check());
    assert_eq!(Ok(()), lim.check());
    // Repeated denied checks leave the state untouched...
    for _ in 0..4 {
        assert!(lim.check().is_err());
    }
    // ...so exactly one cell is available after one interval, not fewer.
    clock.advance(ms(500));
    assert_eq!(Ok(()), lim.check());
    assert!(lim.check().is_err());
}

#[test]
fn generated_check_n_one_equals_check() {
    let clock = FakeRelativeClock::default();
    let singles = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(3u32)), clock.clone());
    let batches = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(3u32)), clock.clone());
    let one = nonzero!(1u32);
    for step in 0..8 {
        let single = singles.check().is_ok();
        let batch = batches.check_n(one).unwrap().is_ok();
        assert_eq!(single, batch, "step {}", step);
        clock.advance(ms(100));
    }
}

#[test]
fn generated_batch_drain_and_deny() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(6u32)), clock.clone());
    assert!(lim.check_n(nonzero!(4u32)).unwrap().is_ok());
    // The remaining two cells conform exactly at the boundary.
    assert!(lim.check_n(nonzero!(2u32)).unwrap().is_ok());
    // The bucket is drained: even a single cell is denied now.
    assert!(lim.check_n(nonzero!(1u32)).unwrap().is_err());
}

#[test]
fn generated_batch_impossible_capacity() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(5u32)), clock.clone());
    assert_eq!(Err(InsufficientCapacity(5)), lim.check_n(nonzero!(6u32)));
    assert_eq!(Err(InsufficientCapacity(5)), lim.check_n(nonzero!(9u32)));
    let err = lim.check_n(nonzero!(11u32)).unwrap_err();
    assert_eq!(err.0, 5);
    assert_eq!(
        format!("{}", err),
        "required number of cells 5 exceeds bucket's capacity"
    );
    // Capacity failures never touch the state: the full burst still fits.
    assert!(lim.check_n(nonzero!(5u32)).unwrap().is_ok());
}

#[test]
fn generated_full_burst_batch_replenish() {
    let clock = FakeRelativeClock::default();
    let quota = Quota::per_second(nonzero!(5u32));
    let lim = RateLimiter::direct_with_clock(quota, clock.clone());
    assert!(lim.check_n(nonzero!(5u32)).unwrap().is_ok());
    assert!(lim.check_n(nonzero!(5u32)).unwrap().is_err());
    // A full-burst batch conforms again after the full replenish figure.
    clock.advance(quota.burst_size_replenished_in());
    assert!(lim.check_n(nonzero!(5u32)).unwrap().is_ok());
}

#[test]
fn generated_partial_regain_batch() {
    let clock = FakeRelativeClock::default();
    // t = 200ms, tau = 800ms
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(5u32)), clock.clone());
    assert!(lim.check_n(nonzero!(5u32)).unwrap().is_ok());
    clock.advance(ms(400));
    // Two cells regained after 400ms: a batch of two conforms at the boundary,
    assert!(lim.check_n(nonzero!(2u32)).unwrap().is_ok());
    // but nothing more is available at this instant.
    assert!(lim.check_n(nonzero!(1u32)).unwrap().is_err());
}

#[test]
fn generated_batch_equals_singles_history() {
    let clock = FakeRelativeClock::default();
    let batch = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    let singles = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone());
    assert!(batch.check_n(nonzero!(3u32)).unwrap().is_ok());
    for _ in 0..3 {
        assert_eq!(Ok(()), singles.check());
    }
    // Both histories leave identical state: same next outcome, same denial.
    assert_eq!(Ok(()), batch.check());
    assert_eq!(Ok(()), singles.check());
    let nb = batch.check().unwrap_err();
    let ns_ = singles.check().unwrap_err();
    assert_eq!(nb.earliest_possible(), ns_.earliest_possible());
    assert_eq!(
        nb.wait_time_from(clock.now()),
        ns_.wait_time_from(clock.now())
    );
}
