// Construction surface: constants, integer constructors, limb assembly.

#[test]
fn generated_constants_render() {
    assert_eq!(Decimal::ZERO.to_string(), "0");
    assert_eq!(Decimal::ONE.to_string(), "1");
    assert_eq!(Decimal::NEGATIVE_ONE.to_string(), "-1");
    assert_eq!(Decimal::TWO.to_string(), "2");
    assert_eq!(Decimal::TEN.to_string(), "10");
    assert_eq!(Decimal::ONE_HUNDRED.to_string(), "100");
    assert_eq!(Decimal::ONE_THOUSAND.to_string(), "1000");
    assert_eq!(Decimal::MAX_SCALE, 28);
    assert_eq!(Decimal::default(), Decimal::ZERO);
    assert_eq!(Decimal::default().to_string(), "0");
}

#[test]
fn generated_domain_bounds_render() {
    assert_eq!(Decimal::MAX.to_string(), "79228162514264337593543950335");
    assert_eq!(Decimal::MIN.to_string(), "-79228162514264337593543950335");
    assert_eq!(Decimal::MIN, -Decimal::MAX);
    assert_eq!(Decimal::MAX.scale(), 0);
}

#[test]
fn generated_new_scale_forms() {
    assert_eq!(Decimal::new(3141, 3).to_string(), "3.141");
    assert_eq!(Decimal::new(-5, 1).to_string(), "-0.5");
    assert_eq!(Decimal::new(5000, 3).to_string(), "5.000");
    assert_eq!(Decimal::new(5000, 3).scale(), 3);
    assert_eq!(Decimal::new(0, 2).to_string(), "0.00");
    assert_eq!(Decimal::new(7, 0).to_string(), "7");
}

#[test]
fn generated_try_new_paths() {
    let ok: rust_decimal::Result<Decimal> = Decimal::try_new(1234, 2);
    assert_eq!(ok.unwrap().to_string(), "12.34");
    assert_eq!(
        Decimal::try_new(1234, 30),
        Err(Error::ScaleExceedsMaximumPrecision(30))
    );
}

#[test]
fn generated_new_panics_on_bad_scale() {
    assert!(panics(|| Decimal::new(1, 99)));
    // paired positive assertion so a panic-everywhere stub still fails
    assert_eq!(Decimal::new(1, 2).to_string(), "0.01");
}

#[test]
fn generated_from_i128_with_scale_ok() {
    assert_eq!(Decimal::from_i128_with_scale(5000, 3).to_string(), "5.000");
    assert_eq!(
        Decimal::from_i128_with_scale(-987654321012345678901234567, 9).to_string(),
        "-987654321012345678.901234567"
    );
}

#[test]
fn generated_try_from_i128_errors() {
    assert_eq!(
        Decimal::try_from_i128_with_scale(1, 42),
        Err(Error::ScaleExceedsMaximumPrecision(42))
    );
    assert_eq!(
        Decimal::try_from_i128_with_scale(i128::MAX, 0),
        Err(Error::ExceedsMaximumPossibleValue)
    );
    assert_eq!(
        Decimal::try_from_i128_with_scale(i128::MIN, 0),
        Err(Error::LessThanMinimumPossibleValue)
    );
    assert_eq!(
        Decimal::try_from_i128_with_scale(1250, 2).unwrap().to_string(),
        "12.50"
    );
}

#[test]
fn generated_from_i128_panics_out_of_domain() {
    assert!(panics(|| Decimal::from_i128_with_scale(i128::MAX, 0)));
    assert_eq!(Decimal::from_i128_with_scale(125, 2).to_string(), "1.25");
}

#[test]
fn generated_from_parts_limbs() {
    assert_eq!(
        Decimal::from_parts(1, 2, 3, false, 4).to_string(),
        "5534023222971858.9441"
    );
    assert_eq!(Decimal::from_parts(125, 0, 0, true, 2).to_string(), "-1.25");
    assert_eq!(Decimal::from_parts(0, 0, 0, false, 0), Decimal::ZERO);
}

#[test]
fn generated_from_integer_impls() {
    assert_eq!(Decimal::from(42u8).to_string(), "42");
    assert_eq!(Decimal::from(-42i8).to_string(), "-42");
    assert_eq!(Decimal::from(42u16).to_string(), "42");
    assert_eq!(Decimal::from(-42i16).to_string(), "-42");
    assert_eq!(Decimal::from(42u32).to_string(), "42");
    assert_eq!(Decimal::from(-42i32).to_string(), "-42");
    assert_eq!(Decimal::from(42u64).to_string(), "42");
    assert_eq!(Decimal::from(-42i64).to_string(), "-42");
    assert_eq!(Decimal::from(42usize).to_string(), "42");
    assert_eq!(Decimal::from(-42isize).to_string(), "-42");
    assert_eq!(Decimal::from(-42i128).to_string(), "-42");
    assert_eq!(Decimal::from(42u128).to_string(), "42");
    assert_eq!(Decimal::from(9_007_199_254_740_993_u64).scale(), 0);
}

#[test]
fn generated_from_int128_panics_on_overflow() {
    assert!(panics(|| Decimal::from(1u128 << 100)));
    assert_eq!(Decimal::from(1u128 << 20).to_string(), "1048576");
}
