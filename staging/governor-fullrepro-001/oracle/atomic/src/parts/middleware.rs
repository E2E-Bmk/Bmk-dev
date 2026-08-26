// Middleware and snapshots: capacity countdown/regain/idle-reset, quota
// reconstruction, the default unit outcome, caller-defined middleware.

use governor::middleware::{RateLimitingMiddleware, StateSnapshot};

#[derive(Debug)]
struct TicketStamp;

impl RateLimitingMiddleware<Nanos> for TicketStamp {
    type PositiveOutcome = u64;
    fn allow<K>(_key: &K, _state: impl Into<StateSnapshot>) -> Self::PositiveOutcome {
        4242
    }

    type NegativeOutcome = ();
    fn disallow<K>(_key: &K, _state: impl Into<StateSnapshot>, _start_time: Nanos) {}
}

#[test]
fn generated_snapshot_countdown_and_deny() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(5u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    for expected in [4u32, 3, 2, 1, 0] {
        assert_eq!(
            Ok(expected),
            lim.check().map(|snap| snap.remaining_burst_capacity())
        );
    }
    assert!(lim.check().is_err());
}

#[test]
fn generated_snapshot_regained_cell_consumed() {
    let clock = FakeRelativeClock::default();
    // t = 250ms
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    for _ in 0..4 {
        assert!(lim.check().is_ok());
    }
    clock.advance(ms(250));
    // One cell regained, immediately consumed by this check: zero remains.
    assert_eq!(Ok(0), lim.check().map(|s| s.remaining_burst_capacity()));
    // Fully replenished after a long idle: back to burst - 1.
    clock.advance(Duration::from_secs(20));
    assert_eq!(Ok(3), lim.check().map(|s| s.remaining_burst_capacity()));
}

#[test]
fn generated_snapshot_quota_reconstruction() {
    let clock = FakeRelativeClock::default();
    let per_second = Quota::per_second(nonzero!(5u32));
    let lim = RateLimiter::direct_with_clock(per_second, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    assert_eq!(lim.check().unwrap().quota(), per_second);

    let derived = Quota::with_period(ms(110)).unwrap().allow_burst(nonzero!(3u32));
    let lim = RateLimiter::direct_with_clock(derived, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    let snap = lim.check().unwrap();
    assert_eq!(snap.quota(), derived);
    assert_eq!(snap.quota().replenish_interval(), ms(110));
    assert_eq!(snap.quota().burst_size().get(), 3);
}

#[test]
fn generated_denials_unchanged_by_middleware() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    let _ = lim.check();
    let denial = lim.check().unwrap_err();
    assert_eq!(denial.earliest_possible(), Nanos::new(1_000_000_000));
    assert_eq!(format!("{}", denial), "rate-limited until Nanos(1s)");
}

#[test]
fn generated_custom_middleware_outcomes() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone())
        .with_middleware::<TicketStamp>();
    assert_eq!(Ok(4242), lim.check());
    assert_eq!(Ok(4242), lim.check());
    assert_eq!(Err(()), lim.check());
}

#[test]
fn generated_keyed_snapshot_per_key() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(3u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    assert_eq!(
        Ok(2),
        lim.check_key(&"tenant-a").map(|s| s.remaining_burst_capacity())
    );
    let snap = lim.check_key_n(&"tenant-a", nonzero!(2u32)).unwrap().unwrap();
    assert_eq!(snap.remaining_burst_capacity(), 0);
    // Another key still has its full budget.
    assert_eq!(
        Ok(2),
        lim.check_key(&"tenant-b").map(|s| s.remaining_burst_capacity())
    );
}

#[test]
fn generated_noop_unit_outcome() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    let outcome: Result<(), _> = lim.check();
    assert_eq!(Ok(()), outcome);
}

#[test]
fn generated_snapshot_eq_and_clone() {
    let clock = FakeRelativeClock::default();
    let quota = Quota::per_second(nonzero!(4u32));
    let a = RateLimiter::direct_with_clock(quota, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    let b = RateLimiter::direct_with_clock(quota, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    let snap_a = a.check().unwrap();
    let snap_b = b.check().unwrap();
    assert_eq!(snap_a, snap_b);
    assert_eq!(snap_a.clone(), snap_b);
    assert!(!format!("{:?}", snap_a).is_empty());
}
