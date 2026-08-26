// Introspection, ordering/hashing, byte image, and primitive conversions.

#[test]
fn generated_image_accessors() {
    let value = d("-0.123456");
    assert_eq!(value.scale(), 6);
    assert_eq!(value.mantissa(), -123456i128);
    assert!(value.is_sign_negative());
    assert!(!value.is_sign_positive());
    assert_eq!(d("87.6500").mantissa(), 876500i128);
    assert_eq!(d("87.6500").scale(), 4);
}

#[test]
fn generated_zero_and_integer_predicates() {
    assert!(d("0.000").is_zero());
    assert!(d("-0.0").is_zero());
    assert!(!d("0.001").is_zero());
    assert!(d("1.000").is_integer());
    assert!(d("500").is_integer());
    assert!(!d("1.1").is_integer());
    assert!(!d("0.5").is_integer());
    assert!(d("0.00").is_integer());
}

#[test]
fn generated_sign_mutators_abs_signum() {
    let mut value = d("3.5");
    value.set_sign_negative(true);
    assert_eq!(value.to_string(), "-3.5");
    value.set_sign_positive(true);
    assert_eq!(value.to_string(), "3.5");
    assert_eq!(d("-4.2").abs().to_string(), "4.2");
    assert_eq!(d("4.2").abs().to_string(), "4.2");
    assert_eq!(d("4.2").signum(), Decimal::ONE);
    assert_eq!(d("-4.2").signum().to_string(), "-1");
    assert_eq!(Decimal::ZERO.signum(), Decimal::ZERO);
    assert_eq!((-Decimal::ZERO).signum(), Decimal::ZERO);
}

#[test]
fn generated_min_max_by_value() {
    assert_eq!(d("2.5").max(d("2.49")), d("2.5"));
    assert_eq!(d("2.5").min(d("2.49")), d("2.49"));
    assert_eq!(d("-3").max(d("-2")), d("-2"));
    assert_eq!(d("1.0").max(d("1.00")), d("1.0"));
}

#[test]
fn generated_equality_across_scales() {
    assert_eq!(d("1.0"), d("1.00"));
    assert_eq!(d("1.0"), d("1.000"));
    assert_eq!(d("-0.0"), Decimal::ZERO);
    assert_ne!(d("1.0"), d("1.01"));
    assert_eq!(d("3.1400"), d("3.14"));
}

#[test]
fn generated_ordering_total_numeric() {
    assert!(d("3") > d("2.9999"));
    assert!(d("-1") > d("-2"));
    assert!(d("0.001") > Decimal::ZERO);
    assert_eq!(d("1.0").cmp(&d("1.00")), std::cmp::Ordering::Equal);
    let mut values = vec![d("2.5"), d("-1"), d("0.25"), d("2.50"), Decimal::ZERO];
    values.sort();
    let rendered: Vec<String> = values.iter().map(|v| v.to_string()).collect();
    assert_eq!(rendered, vec!["-1", "0", "0.25", "2.5", "2.50"]);
}

#[test]
fn generated_hash_agrees_with_eq() {
    assert_eq!(hash_of(&d("1.0")), hash_of(&d("1.00")));
    assert_eq!(hash_of(&d("1.0")), hash_of(&d("1.000")));
    assert_eq!(hash_of(&d("-0.0")), hash_of(&Decimal::ZERO));
    assert_ne!(hash_of(&d("1.0")), hash_of(&d("1.01")));
    use std::collections::HashSet;
    let mut set = HashSet::new();
    set.insert(d("2.50"));
    assert!(set.contains(&d("2.5")));
    assert!(!set.contains(&d("2.51")));
}

#[test]
fn generated_serialize_byte_layout() {
    let bytes = d("1.25").serialize();
    assert_eq!(bytes, [0, 0, 2, 0, 125, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
    let negative = d("-1.25").serialize();
    assert_eq!(negative, [0, 0, 2, 128, 125, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
    assert_eq!(d("256").serialize(), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
    assert_eq!(Decimal::ZERO.serialize(), [0u8; 16]);
}

#[test]
fn generated_serialize_deserialize_round_trip() {
    for input in ["1.25", "-1.25", "0.0000000000000000000000000001", "79228162514264337593543950335", "-0.000", "42"] {
        let value = d(input);
        let back = Decimal::deserialize(value.serialize());
        assert_eq!(back, value, "value mismatch for {input}");
        assert_eq!(back.scale(), value.scale(), "scale mismatch for {input}");
        assert_eq!(back.is_sign_negative(), value.is_sign_negative(), "sign mismatch for {input}");
        assert_eq!(back.to_string(), value.to_string(), "render mismatch for {input}");
    }
}

#[test]
fn generated_to_integer_truncates_toward_zero() {
    assert_eq!(d("2.99").to_i64(), Some(2));
    assert_eq!(d("-2.99").to_i64(), Some(-2));
    assert_eq!(d("2.99").to_u64(), Some(2));
    assert_eq!(d("7.5").to_i32(), Some(7));
    assert_eq!(d("200.999").to_u8(), Some(200));
    assert_eq!(d("-1").to_i8(), Some(-1));
    assert_eq!(d("1000").to_i128(), Some(1000));
    assert_eq!(d("1000").to_u128(), Some(1000));
    assert_eq!(d("64").to_isize(), Some(64));
    assert_eq!(d("64").to_usize(), Some(64));
}

#[test]
fn generated_to_integer_out_of_range() {
    assert_eq!(d("-1").to_u64(), None);
    assert_eq!(Decimal::MAX.to_i32(), None);
    assert_eq!(d("256").to_u8(), None);
    assert_eq!(d("128").to_i8(), None);
    assert_eq!(d("-129").to_i8(), None);
    assert_eq!(Decimal::MAX.to_i128(), Some(79228162514264337593543950335i128));
    assert_eq!(Decimal::MIN.to_i128(), Some(-79228162514264337593543950335i128));
}

#[test]
fn generated_to_float() {
    assert_eq!(d("0.1").to_f64(), Some(0.1));
    assert_eq!(d("2.5").to_f32(), Some(2.5f32));
    assert_eq!(d("-3.75").to_f64(), Some(-3.75));
    assert_eq!(Decimal::ZERO.to_f64(), Some(0.0));
}

#[test]
fn generated_try_from_decimal_matches_trait() {
    assert_eq!(i64::try_from(d("2.99")), Ok(2));
    assert_eq!(u32::try_from(d("17.0")), Ok(17));
    assert!(matches!(u64::try_from(d("-1")), Err(Error::ConversionTo(_))));
    assert!(matches!(i32::try_from(Decimal::MAX), Err(Error::ConversionTo(_))));
    assert_eq!(f64::try_from(d("0.1")), Ok(0.1));
}

#[test]
fn generated_infallible_as_forms() {
    assert_eq!(d("2.99").as_i128(), 2);
    assert_eq!(d("-2.99").as_i128(), -2);
    assert_eq!(d("0.1").as_f64(), 0.1);
    assert_eq!(Decimal::MAX.as_i128(), 79228162514264337593543950335i128);
}

#[test]
fn generated_from_integer_primitives() {
    assert_eq!(Decimal::from_i8(-8), Some(d("-8")));
    assert_eq!(Decimal::from_u16(65535), Some(d("65535")));
    assert_eq!(Decimal::from_i64(-9223372036854775808), Some(d("-9223372036854775808")));
    assert_eq!(Decimal::from_u128(79228162514264337593543950335u128), Some(Decimal::MAX));
    assert_eq!(Decimal::from_u128(79228162514264337593543950336u128), None);
    assert_eq!(Decimal::from_i128(i128::MAX), None);
    assert_eq!(Decimal::from_i128(-79228162514264337593543950335i128), Some(Decimal::MIN));
    assert_eq!(Decimal::from_isize(-64), Some(d("-64")));
    assert_eq!(Decimal::from_usize(64), Some(d("64")));
}

#[test]
fn generated_from_infallible_int_conversions() {
    assert_eq!(Decimal::from(7u32).to_string(), "7");
    assert_eq!(Decimal::from(-7i64).to_string(), "-7");
    assert_eq!(Decimal::from(255u8).to_string(), "255");
    assert_eq!(Decimal::from(-128i8).to_string(), "-128");
    assert_eq!(Decimal::from(1_000_000_007usize).to_string(), "1000000007");
}

#[test]
fn generated_from_float_shortest_rendering() {
    assert_eq!(Decimal::from_f64(0.1), Some(d("0.1")));
    assert_eq!(Decimal::from_f64(2.132), Some(d("2.132")));
    assert_eq!(Decimal::from_f32(0.25f32), Some(d("0.25")));
    assert_eq!(Decimal::from_f64(-14.625), Some(d("-14.625")));
    assert_eq!(Decimal::try_from(2.132_f64), Ok(d("2.132")));
    assert_eq!(Decimal::try_from(0.5_f32), Ok(d("0.5")));
}

#[test]
fn generated_from_float_rejects_non_finite() {
    assert_eq!(Decimal::from_f64(f64::NAN), None);
    assert_eq!(Decimal::from_f64(f64::INFINITY), None);
    assert_eq!(Decimal::from_f64(f64::NEG_INFINITY), None);
    assert_eq!(Decimal::from_f64(1e30), None);
    assert_eq!(Decimal::from_f32(f32::NAN), None);
    assert!(matches!(Decimal::try_from(f64::NAN), Err(Error::ConversionTo(_))));
    assert!(matches!(Decimal::try_from(1e30_f64), Err(Error::ConversionTo(_))));
}

#[test]
fn generated_from_float_retain_binary_expansion() {
    assert_eq!(
        Decimal::from_f64_retain(0.1).map(|v| v.to_string()),
        Some("0.1000000000000000055511151231".to_string())
    );
    assert_eq!(
        Decimal::from_f32_retain(0.1f32).map(|v| v.to_string()),
        Some("0.100000001490116119384765625".to_string())
    );
    assert_eq!(Decimal::from_f64_retain(0.5).map(|v| v.to_string()), Some("0.5".to_string()));
    assert_eq!(Decimal::from_f64_retain(f64::NAN), None);
}

#[test]
fn generated_zero_one_trait_surface() {
    assert_eq!(Decimal::zero(), Decimal::ZERO);
    assert!(Decimal::zero().is_zero());
    assert_eq!(Decimal::one(), Decimal::ONE);
    assert!(d("1.00").is_one());
    assert!(!d("1.01").is_one());
    assert_eq!(Decimal::TWO.to_string(), "2");
    assert_eq!(Decimal::TEN.to_string(), "10");
    assert_eq!(Decimal::ONE_HUNDRED.to_string(), "100");
    assert_eq!(Decimal::ONE_THOUSAND.to_string(), "1000");
    assert_eq!(Decimal::NEGATIVE_ONE.to_string(), "-1");
}

#[test]
fn generated_signed_trait_agrees_with_inherent() {
    use rust_decimal::prelude::Signed;
    assert_eq!(Signed::abs(&d("-2.5")).to_string(), "2.5");
    assert_eq!(Signed::signum(&d("-2.5")).to_string(), "-1");
    assert!(Signed::is_negative(&d("-2.5")));
    assert!(Signed::is_positive(&d("2.5")));
    assert_eq!(Signed::is_positive(&Decimal::ZERO), Decimal::ZERO.is_sign_positive());
    assert_eq!(Signed::is_negative(&(-Decimal::ZERO)), (-Decimal::ZERO).is_sign_negative());
}
