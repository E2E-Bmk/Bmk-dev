// Arithmetic surface: operators, scale laws, checked/saturating families.

#[test]
fn generated_add_sub_scale_law() {
    let sum = d("2.50") + d("1.235");
    assert_eq!(sum.to_string(), "3.735");
    assert_eq!(sum.scale(), 3);
    assert_eq!((d("1.5") - d("2.25")).to_string(), "-0.75");
    let zero = d("1.5") - d("1.50");
    assert_eq!(zero.to_string(), "0.00");
    assert_eq!(zero.scale(), 2);
    assert_eq!((d("-1.5") + d("1.5")).to_string(), "0.0");
}

#[test]
fn generated_add_keeps_exact_when_it_fits() {
    let kept = d("79228162514264337593543950.335") + d("0.0000000000000000000000000001");
    assert_eq!(kept.to_string(), "79228162514264337593543950.335");
    assert_eq!(kept.scale(), 3);
}

#[test]
fn generated_add_overflow_rescales_bankers() {
    let reduced = d("7922816251426433759354395033.5") + d("0.1111111111111111111111111111");
    assert_eq!(reduced.to_string(), "7922816251426433759354395034");
    assert_eq!(reduced.scale(), 0);
    let tied = d("79228162514264337593543950334") + d("0.5");
    assert_eq!(tied.to_string(), "79228162514264337593543950334");
}

#[test]
fn generated_max_boundary_add() {
    assert_eq!(Decimal::MAX + d("0.4"), Decimal::MAX);
    assert!(panics(|| Decimal::MAX + d("0.5")));
    assert!(panics(|| Decimal::MAX + Decimal::ONE));
}

#[test]
fn generated_mul_scale_sum() {
    let product = d("2.5") * d("1.25");
    assert_eq!(product.to_string(), "3.125");
    assert_eq!(product.scale(), 3);
    assert_eq!((d("1.5") * d("1.5")).to_string(), "2.25");
    assert_eq!((d("24.95") * Decimal::from(3u32)).to_string(), "74.85");
    assert_eq!((d("-0.04") * d("0.2")).to_string(), "-0.008");
}

#[test]
fn generated_mul_bankers_at_representational_cut() {
    assert_eq!(
        (d("0.6666666666666666666666666666") * d("0.3")).to_string(),
        "0.2000000000000000000000000000"
    );
    assert_eq!(
        (d("0.0000000000000000000000000005") * d("0.5")).to_string(),
        "0.0000000000000000000000000002"
    );
    assert_eq!(
        (d("0.0000000000000000000000000015") * d("0.5")).to_string(),
        "0.0000000000000000000000000008"
    );
    assert_eq!(
        (d("0.0000000000000000000000000025") * d("0.5")).to_string(),
        "0.0000000000000000000000000012"
    );
    assert_eq!(
        (d("0.0000000000000000000000000003") * d("0.5")).to_string(),
        "0.0000000000000000000000000002"
    );
}

#[test]
fn generated_mul_mantissa_overflow_paths() {
    assert_eq!(
        (Decimal::MAX * d("0.5")).to_string(),
        "39614081257132168796771975168"
    );
    assert_eq!(
        (Decimal::MAX * d("0.1")).to_string(),
        "7922816251426433759354395033.5"
    );
    assert!(panics(|| Decimal::MAX * Decimal::TWO));
}

#[test]
fn generated_div_exact_values() {
    assert_eq!(d("10") / d("4"), d("2.5"));
    assert_eq!(d("1") / d("8"), d("0.125"));
    assert_eq!(d("100") / d("8"), d("12.5"));
    assert_eq!(d("2.5") / d("0.5"), d("5"));
    assert_eq!(d("1000") / d("10"), d("100"));
    assert_eq!((d("10") / d("4")).normalize().to_string(), "2.5");
}

#[test]
fn generated_div_inexact_rounds_at_final_digit() {
    assert_eq!(d("2") / d("3"), d("0.6666666666666666666666666667"));
    assert_eq!(d("1") / d("3"), d("0.3333333333333333333333333333"));
    assert_eq!(d("-1") / d("3"), d("-0.3333333333333333333333333333"));
    assert_eq!(d("1") / d("7"), d("0.1428571428571428571428571429"));
    assert_eq!(d("1") / d("6"), d("0.1666666666666666666666666667"));
    assert_eq!(d("5") / d("6"), d("0.8333333333333333333333333333"));
    assert_eq!(d("100") / d("3"), d("33.333333333333333333333333333"));
}

#[test]
fn generated_div_bankers_ties_at_cut() {
    assert_eq!(
        d("3") / d("20000000000000000000000000000"),
        d("0.0000000000000000000000000002")
    );
    assert_eq!(d("1") / d("20000000000000000000000000000"), Decimal::ZERO);
    assert_eq!(
        d("2") / d("30000000000000000000000000000"),
        d("0.0000000000000000000000000001")
    );
}

#[test]
fn generated_zero_divisor_paths() {
    assert_eq!(d("5").checked_div(Decimal::ZERO), None);
    assert_eq!(d("5").checked_rem(Decimal::ZERO), None);
    assert!(panics(|| d("5") / Decimal::ZERO));
    assert!(panics(|| d("5") % Decimal::ZERO));
    assert_eq!(d("5").checked_div(d("2")), Some(d("2.5")));
}

#[test]
fn generated_rem_sign_and_scale() {
    assert_eq!((d("7") % d("3")).to_string(), "1");
    assert_eq!((d("-7") % d("3")).to_string(), "-1");
    assert_eq!((d("7") % d("-3")).to_string(), "1");
    assert_eq!((d("-7") % d("-3")).to_string(), "-1");
    assert_eq!((d("7.25") % d("0.5")).to_string(), "0.25");
    assert_eq!((d("5.00") % d("3")).to_string(), "2.00");
    assert_eq!((d("5") % d("2.5")).to_string(), "0.0");
    assert_eq!((d("2.5") % d("7")).to_string(), "2.5");
    assert_eq!((d("7.5") % d("2")).to_string(), "1.5");
}

#[test]
fn generated_checked_family_matches_operators() {
    assert_eq!(d("2.50").checked_add(d("1.235")), Some(d("3.735")));
    assert_eq!(d("1.5").checked_sub(d("2.25")), Some(d("-0.75")));
    assert_eq!(d("2.5").checked_mul(d("1.25")), Some(d("3.125")));
    assert_eq!(d("7").checked_rem(d("3")), Some(d("1")));
    assert_eq!(Decimal::MAX.checked_add(Decimal::ONE), None);
    assert_eq!(Decimal::MIN.checked_sub(Decimal::ONE), None);
    assert_eq!(Decimal::MAX.checked_mul(Decimal::TWO), None);
}

#[test]
fn generated_saturating_family() {
    assert_eq!(Decimal::MAX.saturating_add(Decimal::ONE), Decimal::MAX);
    assert_eq!(Decimal::MIN.saturating_sub(Decimal::ONE), Decimal::MIN);
    assert_eq!(Decimal::MAX.saturating_mul(Decimal::TWO), Decimal::MAX);
    assert_eq!(Decimal::MAX.saturating_mul(d("-2")), Decimal::MIN);
    assert_eq!(Decimal::MIN.saturating_add(Decimal::ONE), d("-79228162514264337593543950334"));
    assert_eq!(d("1.5").saturating_add(d("0.5")).to_string(), "2.0");
}

#[test]
fn generated_neg_flips_sign_flag() {
    assert_eq!((-d("1.5")).to_string(), "-1.5");
    assert_eq!((-d("-1.5")).to_string(), "1.5");
    let negated_zero = -Decimal::ZERO;
    assert!(negated_zero.is_sign_negative());
    assert_eq!(negated_zero, Decimal::ZERO);
}

#[test]
fn generated_reference_operand_forms() {
    let a = d("1.5");
    let b = d("2.25");
    assert_eq!(&a + &b, d("3.75"));
    assert_eq!(a + &b, d("3.75"));
    assert_eq!(&a - b, d("-0.75"));
    assert_eq!(&a * &b, d("3.375"));
    assert_eq!(&b / &a, d("1.5"));
    assert_eq!(&b % &a, d("0.75"));
}

#[test]
fn generated_assign_operator_chain() {
    let mut value = d("1.5");
    value += d("0.25");
    assert_eq!(value.to_string(), "1.75");
    value *= d("2");
    assert_eq!(value.to_string(), "3.50");
    value -= d("0.5");
    assert_eq!(value.to_string(), "3.00");
    value /= d("3");
    assert_eq!(value.to_string(), "1.00");
    value %= d("0.4");
    assert_eq!(value.to_string(), "0.20");
}

#[test]
fn generated_sum_product_aggregation() {
    let values = vec![d("1.1"), d("2.02"), d("3.003")];
    let total: Decimal = values.iter().copied().sum();
    assert_eq!(total.to_string(), "6.123");
    let product: Decimal = values.iter().copied().product();
    assert_eq!(product.to_string(), "6.672666");
    let empty: Vec<Decimal> = Vec::new();
    assert_eq!(empty.iter().copied().sum::<Decimal>(), Decimal::ZERO);
    assert_eq!(empty.iter().copied().product::<Decimal>(), Decimal::ONE);
    // reference-based aggregation
    let refs = [d("1.5"), d("2.5")];
    let ref_sum: Decimal = refs.iter().sum();
    assert_eq!(ref_sum.to_string(), "4.0");
    let ref_product: Decimal = refs.iter().product();
    assert_eq!(ref_product.to_string(), "3.75");
}
