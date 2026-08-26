// Quotas and time arithmetic: constructor division, truncation, getters,
// with_period/allow_burst, the deprecated constructor, equality, debug form.

#[test]
fn generated_per_second_interval_division() {
    let q = Quota::per_second(nonzero!(4u32));
    assert_eq!(q.replenish_interval(), ms(250));
    assert_eq!(q.burst_size().get(), 4);
    assert_eq!(q.burst_size_replenished_in(), ms(1000));
}

#[test]
fn generated_nanosecond_truncation() {
    let q = Quota::per_second(nonzero!(3u32));
    assert_eq!(q.replenish_interval(), ns(333_333_333));
    // The truncated interval is what multiplies out: not one full second.
    assert_eq!(q.burst_size_replenished_in(), ns(999_999_999));
}

#[test]
fn generated_per_minute_per_hour_intervals() {
    assert_eq!(Quota::per_minute(nonzero!(6u32)).replenish_interval(), ms(10_000));
    assert_eq!(Quota::per_minute(nonzero!(7u32)).replenish_interval(), ns(8_571_428_571));
    assert_eq!(Quota::per_hour(nonzero!(9u32)).replenish_interval(), ms(400_000));
    assert_eq!(Quota::per_hour(nonzero!(9u32)).burst_size().get(), 9);
}

#[test]
fn generated_with_period_and_zero() {
    let q = Quota::with_period(ms(120)).unwrap();
    assert_eq!(q.burst_size().get(), 1);
    assert_eq!(q.replenish_interval(), ms(120));
    assert!(Quota::with_period(Duration::ZERO).is_none());
}

#[test]
fn generated_allow_burst_replaces_only_burst() {
    let q = Quota::with_period(ms(90)).unwrap().allow_burst(nonzero!(7u32));
    assert_eq!(q.burst_size().get(), 7);
    assert_eq!(q.replenish_interval(), ms(90));
    assert_eq!(q.burst_size_replenished_in(), ms(630));
}

#[test]
#[allow(deprecated)]
fn generated_deprecated_new_divides_period() {
    let q = Quota::new(nonzero!(4u32), Duration::from_secs(2)).unwrap();
    assert_eq!(q.replenish_interval(), ms(500));
    assert_eq!(q.burst_size().get(), 4);
    assert!(Quota::new(nonzero!(3u32), Duration::ZERO).is_none());
}

#[test]
fn generated_quota_equality_and_copy() {
    let a = Quota::per_second(nonzero!(2u32));
    let b = Quota::with_period(ms(500)).unwrap().allow_burst(nonzero!(2u32));
    assert_eq!(a, b);
    assert_ne!(a, Quota::per_second(nonzero!(3u32)));
    assert_ne!(a, Quota::with_period(ms(400)).unwrap().allow_burst(nonzero!(2u32)));
    // Copy: using the value twice must compile and compare equal.
    let c = a;
    assert_eq!(a, c);
}

#[test]
fn generated_quota_debug_form() {
    let simple = Quota::with_period(ms(250)).unwrap();
    assert_eq!(
        format!("{:?}", simple),
        "Quota { max_burst: 1, replenish_1_per: 250ms }"
    );
    let truncated = Quota::per_second(nonzero!(3u32));
    assert_eq!(
        format!("{:?}", truncated),
        "Quota { max_burst: 3, replenish_1_per: 333.333333ms }"
    );
}
