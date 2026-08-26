// Clocks and the nanosecond scalar: fake clock semantics, shared clones,
// Nanos conversions and rendering, Reference arithmetic, real-time facts.

#[test]
fn generated_fake_clock_starts_at_zero() {
    let clock = FakeRelativeClock::default();
    assert_eq!(clock.now(), Nanos::new(0));
    assert_eq!(clock.now(), Nanos::from(Duration::ZERO));
}

#[test]
fn generated_fake_clock_advance_and_read() {
    let clock = FakeRelativeClock::default();
    clock.advance(ms(750));
    assert_eq!(clock.now(), Nanos::new(750_000_000));
    clock.advance(ns(250_000_000));
    assert_eq!(clock.now(), Nanos::from(Duration::from_secs(1)));
}

#[test]
fn generated_fake_clock_clones_share() {
    let original = FakeRelativeClock::default();
    let clone = original.clone();
    original.advance(ms(420));
    assert_eq!(clone.now(), Nanos::new(420_000_000));
    clone.advance(ms(80));
    assert_eq!(original.now(), Nanos::new(500_000_000));
}

#[test]
fn generated_fake_clock_equality() {
    let a = FakeRelativeClock::default();
    let b = FakeRelativeClock::default();
    assert_eq!(a, b);
    a.advance(ms(15));
    assert_ne!(a, b);
    b.advance(ms(15));
    assert_eq!(a, b);
}

#[test]
fn generated_nanos_conversions() {
    let n = Nanos::new(1_500_000_000);
    assert_eq!(n, Nanos::from(Duration::from_millis(1500)));
    assert_eq!(n.as_u64(), 1_500_000_000);
    let back: Duration = n.into();
    assert_eq!(back, Duration::from_millis(1500));
    assert_eq!(Nanos::from(7u64).as_u64(), 7);
}

#[test]
fn generated_nanos_debug_wraps_duration() {
    assert_eq!(format!("{:?}", Nanos::new(1_500_000_000)), "Nanos(1.5s)");
    assert_eq!(format!("{:?}", Nanos::from(Duration::from_millis(200))), "Nanos(200ms)");
}

#[test]
fn generated_reference_arithmetic_on_nanos() {
    let later = Nanos::new(900);
    let earlier = Nanos::new(350);
    assert_eq!(later.duration_since(earlier), Nanos::new(550));
    // duration_since saturates when the "earlier" instant is later.
    assert_eq!(earlier.duration_since(later), Nanos::new(0));
    assert_eq!(later.saturating_sub(Nanos::new(150)), Nanos::new(750));
    // Reference requires addition of a nanosecond count.
    assert_eq!(later + Nanos::new(100), Nanos::new(1000));
}

#[test]
fn generated_duration_implements_reference() {
    let later = Duration::from_millis(600);
    let earlier = Duration::from_millis(250);
    assert_eq!(
        Reference::duration_since(&later, earlier),
        Nanos::from(Duration::from_millis(350))
    );
    assert_eq!(Reference::duration_since(&earlier, later), Nanos::new(0));
    assert_eq!(
        Reference::saturating_sub(&later, Nanos::from(Duration::from_millis(100))),
        Duration::from_millis(500)
    );
    // Underflowing subtraction returns the receiver unchanged.
    assert_eq!(
        Reference::saturating_sub(&earlier, Nanos::from(Duration::from_millis(400))),
        earlier
    );
}

#[test]
fn generated_real_clocks_first_checks() {
    let mono = MonotonicClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_hour(nonzero!(1u32)), mono);
    assert_eq!(Ok(()), lim.check());
    assert!(lim.check().is_err());

    let sys = SystemClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_hour(nonzero!(1u32)), sys);
    assert_eq!(Ok(()), lim.check());
    assert!(lim.check().is_err());

    let default_clock = governor::clock::DefaultClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_hour(nonzero!(1u32)), default_clock);
    assert_eq!(Ok(()), lim.check());
    assert!(lim.check().is_err());

    let direct: DefaultDirectRateLimiter = RateLimiter::direct(Quota::per_hour(nonzero!(1u32)));
    assert_eq!(Ok(()), direct.check());
    assert!(direct.check().is_err());
}

#[test]
fn generated_clock_accessor_reflects_advances() {
    let clock = FakeRelativeClock::default();
    let lim = RateLimiter::direct_with_clock(Quota::per_second(nonzero!(1u32)), clock.clone());
    clock.advance(ms(330));
    assert_eq!(lim.clock().now(), Nanos::new(330_000_000));
    assert_eq!(lim.clock().now(), clock.now());
}
