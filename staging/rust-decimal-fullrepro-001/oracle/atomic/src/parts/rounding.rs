// Rounding and scale surgery: round/round_dp, strategy matrix, round_sf,
// trunc/fract, floor/ceil, rescale/set_scale, normalize.

#[test]
fn generated_round_bankers_to_integer() {
    assert_eq!(d("6.5").round().to_string(), "6");
    assert_eq!(d("7.5").round().to_string(), "8");
    assert_eq!(d("-6.5").round().to_string(), "-6");
    assert_eq!(d("-7.5").round().to_string(), "-8");
    assert_eq!(d("2.8").round().to_string(), "3");
    assert_eq!(d("2.4").round().to_string(), "2");
    assert_eq!(d("-2.8").round().to_string(), "-3");
    assert_eq!(d("11").round().to_string(), "11");
}

#[test]
fn generated_round_dp_bankers() {
    assert_eq!(d("1.25").round_dp(1).to_string(), "1.2");
    assert_eq!(d("1.35").round_dp(1).to_string(), "1.4");
    assert_eq!(d("-1.25").round_dp(1).to_string(), "-1.2");
    assert_eq!(d("-1.35").round_dp(1).to_string(), "-1.4");
    assert_eq!(d("3.14159").round_dp(3).to_string(), "3.142");
    assert_eq!(d("0.12345").round_dp(4).to_string(), "0.1234");
    assert_eq!(d("0.12355").round_dp(4).to_string(), "0.1236");
}

#[test]
fn generated_round_dp_no_padding_at_or_above_scale() {
    let value = d("4.6");
    let rounded = value.round_dp(5);
    assert_eq!(rounded.to_string(), "4.6");
    assert_eq!(rounded.scale(), 1);
    let same = value.round_dp(1);
    assert_eq!(same.to_string(), "4.6");
    assert_eq!(same.scale(), 1);
}

#[test]
fn generated_round_dp_matches_nearest_even_strategy() {
    for input in ["1.25", "1.35", "-9.005", "0.0005", "123.456", "2.5"] {
        let value = d(input);
        for dp in [0u32, 1, 2, 3] {
            assert_eq!(
                value.round_dp(dp),
                value.round_dp_with_strategy(dp, RoundingStrategy::MidpointNearestEven),
                "input {input} dp {dp}"
            );
        }
    }
}

#[test]
fn generated_strategy_matrix_positive_midpoint() {
    let value = d("2.35");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointNearestEven).to_string(), "2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointAwayFromZero).to_string(), "2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointTowardZero).to_string(), "2.3");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToZero).to_string(), "2.3");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::AwayFromZero).to_string(), "2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToNegativeInfinity).to_string(), "2.3");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToPositiveInfinity).to_string(), "2.4");
}

#[test]
fn generated_strategy_matrix_negative_midpoint() {
    let value = d("-2.35");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointNearestEven).to_string(), "-2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointAwayFromZero).to_string(), "-2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::MidpointTowardZero).to_string(), "-2.3");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToZero).to_string(), "-2.3");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::AwayFromZero).to_string(), "-2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToNegativeInfinity).to_string(), "-2.4");
    assert_eq!(value.round_dp_with_strategy(1, RoundingStrategy::ToPositiveInfinity).to_string(), "-2.3");
}

#[test]
fn generated_strategy_matrix_below_midpoint() {
    let pos = d("2.34");
    let neg = d("-2.34");
    for strategy in [
        RoundingStrategy::MidpointNearestEven,
        RoundingStrategy::MidpointAwayFromZero,
        RoundingStrategy::MidpointTowardZero,
        RoundingStrategy::ToZero,
        RoundingStrategy::ToNegativeInfinity,
    ] {
        assert_eq!(pos.round_dp_with_strategy(1, strategy).to_string(), "2.3");
    }
    assert_eq!(pos.round_dp_with_strategy(1, RoundingStrategy::AwayFromZero).to_string(), "2.4");
    assert_eq!(pos.round_dp_with_strategy(1, RoundingStrategy::ToPositiveInfinity).to_string(), "2.4");
    assert_eq!(neg.round_dp_with_strategy(1, RoundingStrategy::AwayFromZero).to_string(), "-2.4");
    assert_eq!(neg.round_dp_with_strategy(1, RoundingStrategy::ToNegativeInfinity).to_string(), "-2.4");
    assert_eq!(neg.round_dp_with_strategy(1, RoundingStrategy::ToPositiveInfinity).to_string(), "-2.3");
    assert_eq!(neg.round_dp_with_strategy(1, RoundingStrategy::MidpointTowardZero).to_string(), "-2.3");
}

#[test]
fn generated_midpoint_variants_disagree_only_on_exact_half() {
    assert_eq!(d("2.45").round_dp_with_strategy(1, RoundingStrategy::MidpointNearestEven).to_string(), "2.4");
    assert_eq!(d("2.45").round_dp_with_strategy(1, RoundingStrategy::MidpointAwayFromZero).to_string(), "2.5");
    assert_eq!(d("2.451").round_dp_with_strategy(1, RoundingStrategy::MidpointTowardZero).to_string(), "2.5");
    assert_eq!(d("2.450").round_dp_with_strategy(1, RoundingStrategy::MidpointTowardZero).to_string(), "2.4");
    assert_eq!(d("-8.65").round_dp_with_strategy(1, RoundingStrategy::MidpointNearestEven).to_string(), "-8.6");
    assert_eq!(d("-8.65").round_dp_with_strategy(1, RoundingStrategy::MidpointAwayFromZero).to_string(), "-8.7");
}

#[test]
fn generated_round_sf_basic() {
    assert_eq!(d("123.456").round_sf(2), Some(d("120")));
    assert_eq!(d("0.00123").round_sf(2), Some(d("0.0012")));
    assert_eq!(d("999").round_sf(1), Some(d("1000")));
    assert_eq!(d("-123.456").round_sf(4).map(|v| v.to_string()), Some("-123.5".to_string()));
    assert_eq!(d("123.456").round_sf(5).map(|v| v.to_string()), Some("123.46".to_string()));
    assert_eq!(d("87.65").round_sf(3).map(|v| v.to_string()), Some("87.6".to_string()));
}

#[test]
fn generated_round_sf_edges() {
    assert_eq!(d("123.456").round_sf(0), Some(Decimal::ZERO));
    assert_eq!(Decimal::ZERO.round_sf(5), Some(Decimal::ZERO));
    assert_eq!(d("0.00").round_sf(3), Some(Decimal::ZERO));
    assert_eq!(d("123.456").round_sf(9).map(|v| v.to_string()), Some("123.456000".to_string()));
    assert_eq!(Decimal::MAX.round_sf(1), None);
    assert_eq!(Decimal::MIN.round_sf(1), None);
    assert_eq!(d("123.456").round_sf(6).map(|v| v.to_string()), Some("123.456".to_string()));
}

#[test]
fn generated_round_sf_with_strategy() {
    assert_eq!(
        d("987").round_sf_with_strategy(1, RoundingStrategy::ToZero).map(|v| v.to_string()),
        Some("900".to_string())
    );
    assert_eq!(
        d("987").round_sf_with_strategy(1, RoundingStrategy::AwayFromZero).map(|v| v.to_string()),
        Some("1000".to_string())
    );
    assert_eq!(
        d("0.04567").round_sf_with_strategy(2, RoundingStrategy::ToZero).map(|v| v.to_string()),
        Some("0.045".to_string())
    );
    assert_eq!(
        d("-987").round_sf_with_strategy(1, RoundingStrategy::ToPositiveInfinity).map(|v| v.to_string()),
        Some("-900".to_string())
    );
}

#[test]
fn generated_trunc_and_fract() {
    assert_eq!(d("2.8").trunc().to_string(), "2");
    assert_eq!(d("-2.8").trunc().to_string(), "-2");
    assert_eq!(d("2.8").trunc().scale(), 0);
    assert_eq!(d("2.8").fract().to_string(), "0.8");
    assert_eq!(d("-2.8").fract().to_string(), "-0.8");
    let int_fract = d("14").fract();
    assert_eq!(int_fract.to_string(), "0");
    assert_eq!(int_fract.scale(), 0);
    assert_eq!(d("2.8"), d("2.8").trunc() + d("2.8").fract());
}

#[test]
fn generated_trunc_with_scale() {
    assert_eq!(d("129.845").trunc_with_scale(1).to_string(), "129.8");
    assert_eq!(d("-129.845").trunc_with_scale(2).to_string(), "-129.84");
    assert_eq!(d("129.999").trunc_with_scale(2).to_string(), "129.99");
    assert_eq!(d("1.2").trunc_with_scale(5).to_string(), "1.20000");
    assert_eq!(d("5").trunc_with_scale(2).to_string(), "5.00");
    assert_eq!(d("129.845").trunc_with_scale(3).to_string(), "129.845");
}

#[test]
fn generated_floor_ceil() {
    assert_eq!(d("2.8").floor().to_string(), "2");
    assert_eq!(d("-2.8").floor().to_string(), "-3");
    assert_eq!(d("2.1").ceil().to_string(), "3");
    assert_eq!(d("-2.1").ceil().to_string(), "-2");
    assert_eq!(d("7").floor().to_string(), "7");
    assert_eq!(d("7").ceil().to_string(), "7");
    assert_eq!(d("7.0").ceil().scale(), 0);
    assert_eq!(d("-0.5").floor().to_string(), "-1");
    assert_eq!(d("0.5").ceil().to_string(), "1");
}

#[test]
fn generated_rescale_pads_zeros_up() {
    let mut value = d("1.25");
    value.rescale(4);
    assert_eq!(value.to_string(), "1.2500");
    assert_eq!(value.scale(), 4);
    let mut int_value = d("42");
    int_value.rescale(3);
    assert_eq!(int_value.to_string(), "42.000");
}

#[test]
fn generated_rescale_clamps_at_mantissa_headroom() {
    let mut value = d("1.25");
    value.rescale(99);
    assert_eq!(value.scale(), 28);
    assert_eq!(value, d("1.25"));
    let mut max = Decimal::MAX;
    max.rescale(5);
    assert_eq!(max, Decimal::MAX);
    assert_eq!(max.scale(), 0);
}

#[test]
fn generated_rescale_down_rounds_midpoint_away() {
    let mut value = d("1.25");
    value.rescale(1);
    assert_eq!(value.to_string(), "1.3");
    let mut negative = d("-1.25");
    negative.rescale(1);
    assert_eq!(negative.to_string(), "-1.3");
    assert_eq!(d("1.25").round_dp(1).to_string(), "1.2");
    let mut below = d("1.24");
    below.rescale(1);
    assert_eq!(below.to_string(), "1.2");
}

#[test]
fn generated_set_scale_reinterprets_mantissa() {
    let mut value = d("1.2345");
    assert_eq!(value.set_scale(2), Ok(()));
    assert_eq!(value.to_string(), "123.45");
    let mut int_value = d("335");
    assert_eq!(int_value.set_scale(3), Ok(()));
    assert_eq!(int_value.to_string(), "0.335");
    let mut over = d("7.5");
    assert_eq!(over.set_scale(29), Err(Error::ScaleExceedsMaximumPrecision(29)));
    assert_eq!(over.to_string(), "7.5");
}

#[test]
fn generated_normalize_strips_trailing_zeros() {
    let normalized = d("1.2500").normalize();
    assert_eq!(normalized.to_string(), "1.25");
    assert_eq!(normalized.scale(), 2);
    assert_eq!(d("100").normalize().to_string(), "100");
    assert_eq!(d("100").normalize().scale(), 0);
    assert_eq!(d("3.100").normalize().to_string(), "3.1");
    assert_eq!(d("1.2500").normalize(), d("1.2500"));
}

#[test]
fn generated_normalize_zero_canonical() {
    let mut negative_zero = d("0.000");
    negative_zero.set_sign_negative(true);
    assert!(negative_zero.is_sign_negative());
    let canonical = negative_zero.normalize();
    assert_eq!(canonical.to_string(), "0");
    assert_eq!(canonical.scale(), 0);
    assert!(canonical.is_sign_positive());
    let mut in_place = d("0.0500");
    in_place.normalize_assign();
    assert_eq!(in_place.to_string(), "0.05");
    assert_eq!(in_place.scale(), 2);
}
