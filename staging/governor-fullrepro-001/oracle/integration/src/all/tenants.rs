// Multi-tenant keyed flows: per-key budgets, retention thresholds, store
// family parity, bulk admission accounting.

#[test]
fn generated_tenant_isolation_and_retention() {
    let clock = FakeRelativeClock::default();
    // t = 1s, burst 1
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    assert_eq!(Ok(()), lim.check_key(&"acme")); // TAT = 1s
    clock.advance(ms(400));
    assert_eq!(Ok(()), lim.check_key(&"globex")); // TAT = 1.4s
    clock.advance(ms(500));
    assert_eq!(Ok(()), lim.check_key(&"initech")); // TAT = 1.9s
    // acme's budget is still exhausted at 900ms.
    assert!(lim.check_key(&"acme").is_err());
    assert_eq!(lim.len(), 3);

    // At 2.3s the threshold is 1.3s: only acme's state (TAT 1s) is stale.
    clock.advance(ms(1400));
    lim.retain_recent();
    assert_eq!(lim.len(), 2);

    // The evicted tenant re-enters as first-seen and conforms immediately.
    assert_eq!(Ok(()), lim.check_key(&"acme"));
    assert_eq!(lim.len(), 3);
}

#[test]
fn generated_store_families_agree() {
    let clock = FakeRelativeClock::default();
    let quota = Quota::per_second(nonzero!(3u32));
    let hash_lim = RateLimiter::hashmap_with_clock(quota, clock.clone());
    let dash_lim = RateLimiter::dashmap_with_clock(quota, clock.clone());

    let script: &[(&str, u32, u64)] = &[
        ("edge", 1, 0),
        ("edge", 2, 0),
        ("edge", 1, 50),
        ("core", 3, 0),
        ("core", 1, 200),
        ("edge", 1, 400),
        ("core", 2, 0),
    ];
    for (key, n, advance) in script {
        clock.advance(ms(*advance));
        let n = std::num::NonZeroU32::new(*n).unwrap();
        let h = hash_lim.check_key_n(key, n);
        let d = dash_lim.check_key_n(key, n);
        match (h, d) {
            (Ok(Ok(())), Ok(Ok(()))) => {}
            (Ok(Err(hn)), Ok(Err(dn))) => {
                assert_eq!(hn.earliest_possible(), dn.earliest_possible());
            }
            (Err(he), Err(de)) => assert_eq!(he, de),
            (h, d) => panic!("stores diverged on {}: {:?} vs {:?}", key, h, d),
        }
    }
    assert_eq!(hash_lim.len(), dash_lim.len());
    clock.advance(ms(4000));
    hash_lim.retain_recent();
    dash_lim.retain_recent();
    assert_eq!(hash_lim.len(), dash_lim.len());
    assert_eq!(hash_lim.is_empty(), dash_lim.is_empty());
}

#[test]
fn generated_bulk_admission_accounting() {
    let clock = FakeRelativeClock::default();
    // t = 250ms, tau = 750ms
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(4u32)), clock.clone())
        .with_middleware::<StateInformationMiddleware>();

    // A batch of three leaves exactly one immediate cell.
    let snap = lim.check_key_n(&"batchq", nonzero!(3u32)).unwrap().unwrap();
    assert_eq!(snap.remaining_burst_capacity(), 1);
    assert_eq!(
        Ok(0),
        lim.check_key(&"batchq").map(|s| s.remaining_burst_capacity())
    );

    // Denied now; the advertised wait is exactly one per-cell interval.
    let denial = lim.check_key(&"batchq").unwrap_err();
    assert_eq!(denial.wait_time_from(clock.now()), ms(250));

    // An impossible batch reports capacity and does not create keys.
    assert_eq!(
        Err(InsufficientCapacity(4)),
        lim.check_key_n(&"overflow", nonzero!(5u32))
    );
    assert_eq!(lim.len(), 1);

    clock.advance(ms(250));
    assert_eq!(
        Ok(0),
        lim.check_key(&"batchq").map(|s| s.remaining_burst_capacity())
    );

    // A fresh key still admits its full burst in one batch.
    let snap = lim.check_key_n(&"sidecar", nonzero!(4u32)).unwrap().unwrap();
    assert_eq!(snap.remaining_burst_capacity(), 0);
    assert_eq!(lim.len(), 2);
}

#[test]
fn generated_evicted_key_fresh_state_math() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    assert_eq!(Ok(()), lim.check_key(&"ticker"));
    let old_denial = lim.check_key(&"ticker").unwrap_err();
    assert_eq!(old_denial.earliest_possible(), Nanos::new(1_000_000_000));

    clock.advance(ms(2500));
    lim.retain_recent();
    assert_eq!(lim.len(), 0);

    // After eviction the key's denial math restarts from the current instant.
    assert_eq!(Ok(()), lim.check_key(&"ticker"));
    let new_denial = lim.check_key(&"ticker").unwrap_err();
    assert_eq!(new_denial.earliest_possible(), Nanos::new(3_500_000_000));
    assert!(new_denial.earliest_possible() > old_denial.earliest_possible());
}
