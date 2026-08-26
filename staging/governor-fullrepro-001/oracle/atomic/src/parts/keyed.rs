// Keyed limiters: per-key independence, first-seen state, batch variants,
// population accounting, retention thresholds, both store families, hashers.

#[derive(Clone, Default, Debug)]
struct FoldHasher {
    acc: u64,
}

impl std::hash::Hasher for FoldHasher {
    fn finish(&self) -> u64 {
        self.acc.rotate_left(17) ^ 0x9e37_79b9_7f4a_7c15
    }
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.acc = self.acc.wrapping_mul(31).wrapping_add(b as u64);
        }
    }
}

#[derive(Clone, Default, Debug)]
struct FoldHasherBuilder;

impl std::hash::BuildHasher for FoldHasherBuilder {
    type Hasher = FoldHasher;
    fn build_hasher(&self) -> FoldHasher {
        FoldHasher::default()
    }
}

#[test]
fn generated_keys_independent_budgets() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    for key in ["alpha", "beta"] {
        assert_eq!(Ok(()), lim.check_key(&key));
        assert_eq!(Ok(()), lim.check_key(&key));
        assert!(lim.check_key(&key).is_err());
    }
    // A third key still gets its full burst after the others are drained.
    clock.advance(ms(40));
    assert_eq!(Ok(()), lim.check_key(&"gamma"));
    assert_eq!(Ok(()), lim.check_key(&"gamma"));
    assert!(lim.check_key(&"gamma").is_err());
}

#[test]
fn generated_first_seen_key_unset_state() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    clock.advance(ms(700));
    // First sight of a key behaves as an unset state at the current instant.
    assert_eq!(Ok(()), lim.check_key(&"late"));
    let denial = lim.check_key(&"late").unwrap_err();
    // TAT = 700ms + 1s, so the earliest conforming instant is 1.7s.
    assert_eq!(denial.earliest_possible(), Nanos::new(1_700_000_000));
}

#[test]
fn generated_check_key_n_capacity_precedes_state() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(3u32)), clock.clone());
    assert_eq!(
        Err(InsufficientCapacity(3)),
        lim.check_key_n(&"bulk", nonzero!(4u32))
    );
    // The impossible batch never created the key.
    assert_eq!(lim.len(), 0);
    assert!(lim.check_key_n(&"bulk", nonzero!(3u32)).unwrap().is_ok());
    assert_eq!(lim.len(), 1);
}

#[test]
fn generated_len_and_is_empty() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    assert!(lim.is_empty());
    assert_eq!(lim.len(), 0);
    let _ = lim.check_key(&"one");
    let _ = lim.check_key(&"one");
    let _ = lim.check_key(&"one"); // denied checks do not add keys twice
    assert_eq!(lim.len(), 1);
    let _ = lim.check_key(&"two");
    let _ = lim.check_key(&"three");
    assert_eq!(lim.len(), 3);
    assert!(!lim.is_empty());
}

#[test]
fn generated_retain_recent_exact_boundary() {
    // t = 1s; a key checked once at time 0 stores TAT = 1s.
    let at_boundary = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), at_boundary.clone());
    let _ = lim.check_key(&"sess");
    at_boundary.advance(ms(2000)); // threshold = 2s - 1s = 1s == TAT: evicted
    lim.retain_recent();
    assert_eq!(lim.len(), 0);

    let just_before = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), just_before.clone());
    let _ = lim.check_key(&"sess");
    just_before.advance(ms(1999)); // threshold = 999ms < TAT: retained
    lim.retain_recent();
    assert_eq!(lim.len(), 1);
}

#[test]
fn generated_retain_recent_staggered_keys() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    let _ = lim.check_key(&"ingest"); // TAT = 1s
    clock.advance(ms(300));
    let _ = lim.check_key(&"render"); // TAT = 1.3s
    clock.advance(ms(500));
    let _ = lim.check_key(&"export"); // TAT = 1.8s
    assert_eq!(lim.len(), 3);

    clock.advance(ms(1400)); // now 2.2s, threshold 1.2s
    lim.retain_recent();
    assert_eq!(lim.len(), 2);

    clock.advance(ms(800)); // now 3.0s, threshold 2.0s
    lim.retain_recent();
    assert_eq!(lim.len(), 0);
    assert!(lim.is_empty());
}

#[test]
fn generated_eviction_resets_key() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    assert_eq!(Ok(()), lim.check_key(&"burst"));
    assert!(lim.check_key(&"burst").is_err());
    clock.advance(ms(2500));
    lim.retain_recent();
    assert_eq!(lim.len(), 0);
    // The evicted key behaves as first-seen again.
    assert_eq!(Ok(()), lim.check_key(&"burst"));
}

#[test]
fn generated_shrink_to_fit_no_decision_effect() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    let _ = lim.check_key(&"stay".to_string());
    let _ = lim.check_key(&"drop".to_string());
    clock.advance(ms(3000));
    let _ = lim.check_key(&"stay".to_string());
    lim.retain_recent();
    lim.shrink_to_fit();
    assert_eq!(lim.len(), 1);
    // Decisions after shrinking follow the same laws.
    assert_eq!(Ok(()), lim.check_key(&"stay".to_string()));
    assert!(lim.check_key(&"stay".to_string()).is_err());
}

#[test]
fn generated_into_state_store_live_keys() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    let _ = lim.check_key(&"first");
    let _ = lim.check_key(&"second");
    let store = lim.into_state_store();
    let map = store.lock();
    let mut keys: Vec<&str> = map.keys().copied().collect();
    keys.sort();
    assert_eq!(keys, vec!["first", "second"]);
}

#[test]
fn generated_dashmap_store_parity() {
    let clock = FakeRelativeClock::default();
    let hash_lim = RateLimiter::hashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    let dash_lim = RateLimiter::dashmap_with_clock(Quota::per_second(nonzero!(2u32)), clock.clone());
    let script: &[(&str, u64)] = &[
        ("job-a", 0),
        ("job-a", 10),
        ("job-a", 10),
        ("job-b", 100),
        ("job-a", 600),
        ("job-b", 300),
    ];
    for (key, advance) in script {
        clock.advance(ms(*advance));
        assert_eq!(
            hash_lim.check_key(key).is_ok(),
            dash_lim.check_key(key).is_ok(),
            "diverged at key {} advance {}",
            key,
            advance
        );
    }
    assert_eq!(hash_lim.len(), dash_lim.len());
    clock.advance(ms(5000));
    hash_lim.retain_recent();
    dash_lim.retain_recent();
    assert_eq!(hash_lim.len(), dash_lim.len());
}

#[test]
fn generated_custom_hasher_families() {
    let clock = FakeRelativeClock::default();
    let hash_lim = RateLimiter::hashmap_with_clock_and_hasher(
        Quota::per_second(nonzero!(3u32)),
        clock.clone(),
        FoldHasherBuilder,
    );
    let dash_lim = RateLimiter::dashmap_with_clock_and_hasher(
        Quota::per_second(nonzero!(3u32)),
        clock.clone(),
        FoldHasherBuilder,
    );
    for key in [11u32, 22u32] {
        assert!(hash_lim.check_key_n(&key, nonzero!(3u32)).unwrap().is_ok());
        assert!(hash_lim.check_key(&key).is_err());
        assert!(dash_lim.check_key_n(&key, nonzero!(3u32)).unwrap().is_ok());
        assert!(dash_lim.check_key(&key).is_err());
    }
    // Real-clock hasher constructors: first checks conform.
    let hh = RateLimiter::hashmap_with_hasher(Quota::per_second(nonzero!(3u32)), FoldHasherBuilder);
    assert_eq!(Ok(()), hh.check_key(&5u32));
    let dh = RateLimiter::dashmap_with_hasher(Quota::per_second(nonzero!(3u32)), FoldHasherBuilder);
    assert_eq!(Ok(()), dh.check_key(&5u32));
}

#[test]
fn generated_ratelimiter_new_explicit_store() {
    let clock = FakeRelativeClock::default();
    let store: HashMapStateStore<&str> = HashMapStateStore::new(Default::default());
    let lim: RateLimiter<
        &str,
        HashMapStateStore<&str>,
        FakeRelativeClock,
        governor::middleware::NoOpMiddleware<Nanos>,
    > = RateLimiter::new(Quota::per_second(nonzero!(2u32)), store, clock.clone());
    assert_eq!(Ok(()), lim.check_key(&"direct-store"));
    assert_eq!(Ok(()), lim.check_key(&"direct-store"));
    assert!(lim.check_key(&"direct-store").is_err());
    assert_eq!(lim.len(), 1);
}

#[test]
fn generated_keyed_default_alias() {
    let lim: DefaultKeyedRateLimiter<u32> = RateLimiter::keyed(Quota::per_second(nonzero!(2u32)));
    assert_eq!(Ok(()), lim.check_key(&404));
    assert_eq!(lim.len(), 1);
    assert_eq!(Ok(()), lim.check_key(&500));
    assert_eq!(lim.len(), 2);
    let dash = RateLimiter::dashmap(Quota::per_second(nonzero!(2u32)));
    assert_eq!(Ok(()), dash.check_key(&"explicit"));
    assert_eq!(dash.len(), 1);
}
