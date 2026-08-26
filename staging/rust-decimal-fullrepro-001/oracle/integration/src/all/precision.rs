// High-precision flows at the edge of the 96-bit/28-place domain:
// exact vs rounding parse modes, division at the precision limit,
// checked/saturating boundary behavior chained with rendering.

#[test]
fn generated_exact_vs_rounding_parse_pipeline() {
    let text = "0.12345678901234567890123456785";
    assert_eq!(Decimal::from_str_exact(text), Err(Error::Underflow));
    let rounded: Decimal = text.parse().unwrap();
    assert_eq!(rounded.to_string(), "0.1234567890123456789012345679");
    assert_eq!(rounded.scale(), 28);
    let doubled = rounded + rounded;
    assert_eq!(doubled.to_string(), "0.2469135780246913578024691358");
    assert_eq!(doubled.round_dp(5).to_string(), "0.24691");
}

#[test]
fn generated_smallest_positive_unit_flow() {
    let epsilon = Decimal::from_str_exact("0.0000000000000000000000000001").unwrap();
    assert_eq!(epsilon.scale(), 28);
    assert_eq!(epsilon.mantissa(), 1);
    let half = epsilon / d("2");
    assert_eq!(half, Decimal::ZERO);
    let doubled = epsilon * d("2");
    assert_eq!(doubled.to_string(), "0.0000000000000000000000000002");
    assert_eq!(epsilon.normalize(), epsilon);
    assert_eq!(format!("{:e}", epsilon), "1e-28");
}

#[test]
fn generated_max_boundary_saturation_chain() {
    let near_max = Decimal::MAX - d("0.9");
    assert_eq!(near_max.to_string(), "79228162514264337593543950334");
    assert_eq!(near_max.checked_add(d("1.6")), None);
    assert_eq!(near_max.saturating_add(d("1.6")), Decimal::MAX);
    assert_eq!(near_max.checked_add(d("0.4")).map(|v| v.to_string()),
        Some("79228162514264337593543950334".to_string()));
    assert_eq!(Decimal::MAX.mantissa(), 79228162514264337593543950335i128);
    assert_eq!(Decimal::MAX.scale(), 0);
    assert_eq!(Decimal::MIN, -Decimal::MAX);
}

#[test]
fn generated_division_precision_then_reround() {
    let third = Decimal::ONE / d("3");
    assert_eq!(third.to_string(), "0.3333333333333333333333333333");
    let recombined = third * d("3");
    assert_eq!(recombined.to_string(), "0.9999999999999999999999999999");
    assert_ne!(recombined, Decimal::ONE);
    assert_eq!(recombined.round_dp(27), Decimal::ONE);
    assert_eq!(recombined.round_sf(5), Some(d("1.0000")));
    assert_eq!((Decimal::ONE - recombined).mantissa(), 1);
}

#[test]
fn generated_scale_28_arithmetic_rounds_to_fit() {
    let fine = d("0.1111111111111111111111111111");
    let coarse_shift = fine + d("7922816251426433759354395033");
    assert_eq!(coarse_shift.to_string(), "7922816251426433759354395033.1");
    assert_eq!(coarse_shift.scale(), 1);
    let tie = d("79228162514264337593543950334") + d("0.5");
    assert_eq!(tie.to_string(), "79228162514264337593543950334");
    let over = d("79228162514264337593543950335");
    assert_eq!(over.checked_add(d("0.5")), None);
}

#[test]
fn generated_sf_rounding_versus_dp_on_same_value() {
    let value = d("2") / d("7");
    assert_eq!(value.to_string(), "0.2857142857142857142857142857");
    assert_eq!(value.round_dp(6).to_string(), "0.285714");
    assert_eq!(value.round_sf(6).map(|v| v.to_string()), Some("0.285714".to_string()));
    assert_eq!(value.round_sf(3).map(|v| v.to_string()), Some("0.286".to_string()));
    let scaled = value * Decimal::ONE_THOUSAND;
    assert_eq!(scaled.round_sf(3).map(|v| v.to_string()), Some("286".to_string()));
    assert_eq!(scaled.round_dp(3).to_string(), "285.714");
    assert_eq!(scaled.trunc().to_string(), "285");
}

#[test]
fn generated_rescale_headroom_walk() {
    let mut value = d("1234567890.123456789");
    assert_eq!(value.scale(), 9);
    value.rescale(19);
    assert_eq!(value.scale(), 19);
    assert_eq!(value.to_string(), "1234567890.1234567890000000000");
    value.rescale(40);
    assert!(value.scale() < 40);
    assert_eq!(value, d("1234567890.123456789"));
    value.rescale(2);
    assert_eq!(value.to_string(), "1234567890.12");
    let mut midpoint = d("0.125");
    midpoint.rescale(2);
    assert_eq!(midpoint.to_string(), "0.13");
    assert_eq!(d("0.125").round_dp(2).to_string(), "0.12");
}
