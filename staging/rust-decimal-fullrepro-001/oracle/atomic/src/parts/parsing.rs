// Parsing surface: FromStr, from_str_exact, from_str_radix, from_scientific.

#[test]
fn generated_fromstr_basic_scale() {
    assert_eq!(d("1.50").to_string(), "1.50");
    assert_eq!(d("1.50").scale(), 2);
    assert_eq!(d("0.500").scale(), 3);
    assert_eq!(d("5.").to_string(), "5");
    assert_eq!(d("5.").scale(), 0);
    assert_eq!(d(".5").to_string(), "0.5");
    assert_eq!(d("+5.3").to_string(), "5.3");
    assert_eq!(d("-12.750").to_string(), "-12.750");
}

#[test]
fn generated_fromstr_underscores() {
    assert_eq!(d("1_000.25").to_string(), "1000.25");
    assert_eq!(d("1_0.2_5").to_string(), "10.25");
    assert_eq!(d("1_").to_string(), "1");
    assert!(matches!(
        Decimal::from_str("_1"),
        Err(Error::ErrorString(_))
    ));
}

#[test]
fn generated_fromstr_29digit_rounding_away() {
    // midpoint-away-from-zero at the 29th fractional digit
    assert_eq!(
        d("0.00000000000000000000000000025").to_string(),
        "0.0000000000000000000000000003"
    );
    assert_eq!(
        d("0.00000000000000000000000000035").to_string(),
        "0.0000000000000000000000000004"
    );
    assert_eq!(
        d("0.000000000000000000000000000251").to_string(),
        "0.0000000000000000000000000003"
    );
    assert_eq!(
        d("0.32500000000000000000000000005").to_string(),
        "0.3250000000000000000000000001"
    );
    assert_eq!(
        d("0.99999999999999999999999999995").to_string(),
        "1.0000000000000000000000000000"
    );
    assert_eq!(
        d("0.99999999999999999999999999994").to_string(),
        "0.9999999999999999999999999999"
    );
    assert_eq!(
        d("0.00000000000000000000000000001").to_string(),
        "0.0000000000000000000000000000"
    );
}

#[test]
fn generated_fromstr_scientific_forms() {
    assert_eq!(d("1.2e3").to_string(), "1200");
    assert_eq!(d("1.2e3").scale(), 0);
    assert_eq!(d("1e2").to_string(), "100");
    assert_eq!(d("1.2e-2").to_string(), "0.012");
    assert_eq!(d("1.2e+2").to_string(), "120");
    assert_eq!(
        Decimal::from_str("1e29"),
        Err(Error::ScaleExceedsMaximumPrecision(29))
    );
    assert_eq!(
        Decimal::from_str("1e-29"),
        Err(Error::ScaleExceedsMaximumPrecision(29))
    );
}

#[test]
fn generated_fromstr_error_variants() {
    assert!(matches!(Decimal::from_str(""), Err(Error::ErrorString(_))));
    assert!(matches!(Decimal::from_str("-"), Err(Error::ErrorString(_))));
    assert!(matches!(
        Decimal::from_str("1..2"),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_str("abc"),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_str("- 1"),
        Err(Error::ErrorString(_))
    ));
    // integer part exceeding the 96-bit mantissa domain
    assert!(matches!(
        Decimal::from_str("79228162514264337593543950336"),
        Err(Error::ErrorString(_))
    ));
}

#[test]
fn generated_from_str_exact_paths() {
    assert_eq!(Decimal::from_str_exact("0.001").unwrap().to_string(), "0.001");
    assert_eq!(
        Decimal::from_str_exact("0.00000_00000_00000_00000_00000_001")
            .unwrap()
            .to_string(),
        "0.0000000000000000000000000001"
    );
    assert_eq!(
        Decimal::from_str_exact("0.00000000000000000000000000025"),
        Err(Error::Underflow)
    );
    assert_eq!(
        Decimal::from_str_exact("0.99999999999999999999999999995"),
        Err(Error::Underflow)
    );
}

#[test]
fn generated_tryfrom_str_matches_fromstr() {
    let via_try: Decimal = TryFrom::try_from("6.125").unwrap();
    assert_eq!(via_try, d("6.125"));
    assert_eq!(via_try.scale(), 3);
    let bad: Result<Decimal, Error> = TryFrom::try_from("6..125");
    assert!(matches!(bad, Err(Error::ErrorString(_))));
}

#[test]
fn generated_from_str_radix_integers() {
    assert_eq!(Decimal::from_str_radix("ff", 16).unwrap().to_string(), "255");
    assert_eq!(Decimal::from_str_radix("A", 16).unwrap().to_string(), "10");
    assert_eq!(Decimal::from_str_radix("1011", 2).unwrap().to_string(), "11");
    assert_eq!(Decimal::from_str_radix("zz", 36).unwrap().to_string(), "1295");
    assert_eq!(Decimal::from_str_radix("777", 8).unwrap().to_string(), "511");
}

#[test]
fn generated_from_str_radix_ten_matches_fromstr() {
    assert_eq!(Decimal::from_str_radix("12.34", 10).unwrap(), d("12.34"));
    assert_eq!(Decimal::from_str_radix("12.34", 10).unwrap().scale(), 2);
    assert_eq!(Decimal::from_str_radix("-0.500", 10).unwrap().to_string(), "-0.500");
}

#[test]
fn generated_from_str_radix_errors() {
    assert!(matches!(
        Decimal::from_str_radix("11", 1),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_str_radix("11", 37),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_str_radix("g", 16),
        Err(Error::ErrorString(_))
    ));
}

#[test]
fn generated_from_scientific_paths() {
    assert_eq!(Decimal::from_scientific("9.7e-7").unwrap().to_string(), "0.00000097");
    assert_eq!(Decimal::from_scientific("1.23e3").unwrap().to_string(), "1230");
    assert_eq!(Decimal::from_scientific("1.23e3").unwrap().scale(), 0);
    assert_eq!(Decimal::from_scientific("1.23E3").unwrap().to_string(), "1230");
    assert_eq!(
        Decimal::from_scientific("5e28").unwrap().to_string(),
        "50000000000000000000000000000"
    );
    assert_eq!(
        Decimal::from_scientific("1e-28").unwrap().to_string(),
        "0.0000000000000000000000000001"
    );
}

#[test]
fn generated_from_scientific_errors() {
    assert!(matches!(
        Decimal::from_scientific("12"),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_scientific("e3"),
        Err(Error::ErrorString(_))
    ));
    assert!(matches!(
        Decimal::from_scientific("1.23e"),
        Err(Error::ErrorString(_))
    ));
    assert_eq!(
        Decimal::from_scientific("5e-30"),
        Err(Error::ScaleExceedsMaximumPrecision(30))
    );
}

#[test]
fn generated_from_scientific_lossy_rounds() {
    assert_eq!(
        Decimal::from_scientific_lossy("1.234567890123456789012345678901e-5")
            .unwrap()
            .to_string(),
        "0.0000123456789012345678901235"
    );
    assert_eq!(
        Decimal::from_scientific_lossy("2.5e2").unwrap().to_string(),
        "250"
    );
    assert_eq!(
        Decimal::from_scientific_lossy("5e-30"),
        Err(Error::ScaleExceedsMaximumPrecision(30))
    );
}

#[test]
fn generated_parse_zero_sign_normalized() {
    assert_eq!(d("-0").to_string(), "0");
    assert!(!d("-0").is_sign_negative());
    assert_eq!(d("-0.0").to_string(), "0.0");
    assert!(!d("-0.0").is_sign_negative());
    assert_eq!(d("-0.0").scale(), 1);
}
