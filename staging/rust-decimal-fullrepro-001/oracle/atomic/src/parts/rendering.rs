// Rendering surface: Display, Debug, precision/width, exponent forms.

#[test]
fn generated_display_trailing_zeros() {
    for text in ["1.50", "0.500", "-12.750", "3.141", "0.00", "1000.25", "7"] {
        assert_eq!(d(text).to_string(), text);
    }
}

#[test]
fn generated_display_precision_truncates() {
    assert_eq!(format!("{:.1}", d("1.29")), "1.2");
    assert_eq!(format!("{:.0}", d("1.99")), "1");
    assert_eq!(format!("{:.1}", d("1.35")), "1.3");
    assert_eq!(format!("{:.1}", d("1.45")), "1.4");
    assert_eq!(format!("{:.2}", d("-1.999")), "-1.99");
    assert_eq!(format!("{:.0}", d("0.5")), "0");
}

#[test]
fn generated_display_precision_pads() {
    assert_eq!(format!("{:.4}", d("1.25")), "1.2500");
    assert_eq!(format!("{:.3}", d("1.25")), "1.250");
    assert_eq!(format!("{:.2}", d("7")), "7.00");
}

#[test]
fn generated_display_width_and_fill() {
    assert_eq!(format!("{:8.2}", d("-1.5")), "   -1.50");
    assert_eq!(format!("{:08.2}", d("-1.5")), "-0001.50");
    assert_eq!(format!("{:>10}", d("-1.5")), "      -1.5");
}

#[test]
fn generated_lowerexp_forms() {
    assert_eq!(format!("{:e}", d("12345.678")), "1.2345678e4");
    assert_eq!(format!("{:e}", d("0.00123")), "1.23e-3");
    assert_eq!(format!("{:e}", Decimal::ONE), "1e0");
    assert_eq!(format!("{:e}", Decimal::ZERO), "0e0");
}

#[test]
fn generated_upperexp_forms() {
    assert_eq!(format!("{:E}", d("12345.678")), "1.2345678E4");
    assert_eq!(format!("{:E}", d("0.00123")), "1.23E-3");
}

#[test]
fn generated_debug_equals_display() {
    for text in ["1.50", "-0.007", "79228162514264337593543950335", "0"] {
        let value = d(text);
        assert_eq!(format!("{:?}", value), format!("{}", value));
    }
}

#[test]
fn generated_array_string_unsigned_magnitude() {
    for text in ["1.50", "1000.25", "0.0000000000000000000000000001"] {
        let value = d(text);
        assert_eq!(value.array_string().as_ref(), value.to_string());
    }
    assert_eq!(d("-0.007").array_string().as_ref(), "0.007");
    assert_eq!(d("-12.75").array_string().as_ref(), "12.75");
}

#[test]
fn generated_negative_zero_renders_sign() {
    let mut negative_zero = d("0.00");
    negative_zero.set_sign_negative(true);
    assert_eq!(negative_zero.to_string(), "-0.00");
    assert!(negative_zero.is_sign_negative());
    assert_eq!(negative_zero, Decimal::ZERO);
    assert_eq!(negative_zero.signum(), Decimal::ZERO);
}
