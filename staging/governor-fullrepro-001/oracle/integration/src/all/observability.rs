// Observability flows: rate-limit headers from snapshots, quota
// reconstruction driving new limiters, caller-defined middleware.

use governor::middleware::{RateLimitingMiddleware, StateSnapshot};

#[derive(Debug)]
struct UnitBoth;

impl RateLimitingMiddleware<Nanos> for UnitBoth {
    type PositiveOutcome = ();
    fn allow<K>(_key: &K, _state: impl Into<StateSnapshot>) {}

    type NegativeOutcome = ();
    fn disallow<K>(_key: &K, _state: impl Into<StateSnapshot>, _start_time: Nanos) {}
}

#[test]
fn generated_rate_headers_pipeline() {
    let clock = FakeRelativeClock::default();
    // t = 20s
    let lim = RateLimiter::direct_with_clock(Quota::per_minute(nonzero!(3u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();

    let mut remaining_headers = Vec::new();
    for _ in 0..3 {
        remaining_headers.push(lim.check().unwrap().remaining_burst_capacity());
    }
    assert_eq!(remaining_headers, vec![2, 1, 0]);

    let denial = lim.check().unwrap_err();
    let retry_after = denial.wait_time_from(clock.now());
    assert_eq!(retry_after, Duration::from_secs(20));

    // A client honoring Retry-After conforms, consuming the regained cell.
    clock.advance(retry_after);
    assert_eq!(Ok(0), lim.check().map(|s| s.remaining_burst_capacity()));
}

#[test]
fn generated_quota_recovery_from_snapshot() {
    let clock = FakeRelativeClock::default();
    let quota = Quota::with_period(ms(140)).unwrap().allow_burst(nonzero!(4u32));

    let probe = RateLimiter::direct_with_clock(quota, clock.clone())
        .with_middleware::<StateInformationMiddleware>();
    let rebuilt = probe.check().unwrap().quota();
    assert_eq!(rebuilt, quota);
    assert_eq!(rebuilt.replenish_interval(), ms(140));
    assert_eq!(rebuilt.burst_size().get(), 4);

    // Two fresh limiters, one on the original quota and one on the rebuilt
    // quota, produce identical decision sequences on a shared clock.
    let original = RateLimiter::direct_with_clock(quota, clock.clone());
    let recovered = RateLimiter::direct_with_clock(rebuilt, clock.clone());
    for step in 0..10 {
        let a = original.check();
        let b = recovered.check();
        match (a, b) {
            (Ok(()), Ok(())) => {}
            (Err(da), Err(db)) => {
                assert_eq!(da.earliest_possible(), db.earliest_possible());
                // Denials also reconstruct the quota they were checked under.
                assert_eq!(da.quota(), quota);
            }
            (a, b) => panic!("diverged at step {}: {:?} vs {:?}", step, a, b),
        }
        clock.advance(ms(60));
    }
}

#[test]
fn generated_custom_middleware_gateway() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone())
        .with_middleware::<UnitBoth>();

    // Unit middleware yields unit values in both directions.
    assert_eq!(Ok(()), lim.check_key(&"svc"));
    assert_eq!(Ok(()), lim.check_key(&"svc"));
    assert_eq!(Err(()), lim.check_key(&"svc"));

    // Middleware does not change population accounting or retention.
    assert_eq!(lim.len(), 1);
    clock.advance(ms(3000));
    lim.retain_recent();
    assert_eq!(lim.len(), 0);
    assert_eq!(Ok(()), lim.check_key(&"svc"));
}
