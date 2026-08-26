// Cross-boundary flows: floats and scientific text in, arithmetic in the
// decimal domain, primitives and rendered text out.

#[test]
fn generated_float_ingest_two_modes_diverge() {
    let shortest = Decimal::from_f64(0.1).unwrap();
    let retained = Decimal::from_f64_retain(0.1).unwrap();
    assert_eq!(shortest.to_string(), "0.1");
    assert_eq!(retained.to_string(), "0.1000000000000000055511151231");
    assert_ne!(shortest, retained);
    let drift = retained - shortest;
    assert_eq!(drift.to_string(), "0.0000000000000000055511151231");
    assert!(drift > Decimal::ZERO);
    assert_eq!(shortest.to_f64(), Some(0.1));
    assert_eq!(drift.round_dp(10), Decimal::ZERO.round_dp(10));
}

#[test]
fn generated_scientific_ingest_to_fixed_report() {
    let micro = Decimal::from_scientific("9.7e-7").unwrap();
    assert_eq!(micro.to_string(), "0.00000097");
    assert_eq!(micro.scale(), 8);
    let million = Decimal::from_scientific("1.5e6").unwrap();
    assert_eq!(million.to_string(), "1500000");
    let product = micro * million;
    assert_eq!(product.to_string(), "1.45500000");
    assert_eq!(product.normalize().to_string(), "1.455");
    assert_eq!(format!("{:e}", product.normalize()), "1.455e0");
    assert_eq!(format!("{:E}", d("0.00123")), "1.23E-3");
}

#[test]
fn generated_parse_compute_render_exp_round_trip() {
    let start = d("12345.678");
    let scaled = start / Decimal::ONE_THOUSAND;
    assert_eq!(scaled, d("12.345678"));
    let exp_text = format!("{:e}", d("12345.678"));
    assert_eq!(exp_text, "1.2345678e4");
    let back = Decimal::from_scientific(&exp_text).unwrap();
    assert_eq!(back, start);
    assert_eq!(back.to_string(), "12345.678");
    assert_eq!(Decimal::from_scientific("1e-30"),
        Err(Error::ScaleExceedsMaximumPrecision(30)));
}

#[test]
fn generated_integer_export_after_arithmetic() {
    let price = d("19.99");
    let count = Decimal::from_u16(37).unwrap();
    let total = price * count;
    assert_eq!(total.to_string(), "739.63");
    assert_eq!(total.trunc().to_i64(), Some(739));
    assert_eq!(total.ceil().to_u32(), Some(740));
    assert_eq!(u16::try_from(total.round()), Ok(740));
    assert_eq!(total.to_u8(), None);
    assert!(matches!(u8::try_from(total), Err(Error::ConversionTo(_))));
    assert_eq!(total.as_i128(), 739);
}

#[test]
fn generated_radix_ingest_arithmetic_export() {
    let hex = Decimal::from_str_radix("ff", 16).unwrap();
    let binary = Decimal::from_str_radix("1011", 2).unwrap();
    let base36 = Decimal::from_str_radix("zz", 36).unwrap();
    assert_eq!(hex.to_string(), "255");
    assert_eq!(binary.to_string(), "11");
    assert_eq!(base36.to_string(), "1295");
    let combined = hex * binary + base36;
    assert_eq!(combined.to_string(), "4100");
    assert_eq!(combined.to_u16(), Some(4100));
    assert_eq!(combined / d("8"), d("512.5"));
    assert!(Decimal::from_str_radix("12", 1).is_err());
    assert!(matches!(Decimal::from_str_radix("9", 8), Err(Error::ErrorString(_))));
}

#[test]
fn generated_hash_map_keyed_accumulation() {
    use std::collections::HashMap;
    let mut totals: HashMap<Decimal, Decimal> = HashMap::new();
    let orders = [
        (d("0.5"), d("10.00")),
        (d("0.50"), d("2.50")),
        (d("1.25"), d("4.00")),
    ];
    for (rate, amount) in orders {
        *totals.entry(rate).or_insert(Decimal::ZERO) += amount;
    }
    assert_eq!(totals.len(), 2);
    assert_eq!(totals[&d("0.500")].to_string(), "12.50");
    assert_eq!(totals[&d("1.25")], d("4"));
    let grand: Decimal = totals.values().copied().sum();
    assert_eq!(grand.to_string(), "16.50");
    assert_eq!(grand.to_f32(), Some(16.5f32));
}

#[test]
fn generated_underscore_ledger_parse_and_fold() {
    let entries = ["1_000.25", "2_500.75", "-1_250.00"];
    let mut total = Decimal::ZERO;
    for entry in entries {
        total += Decimal::try_from(entry).unwrap();
    }
    assert_eq!(total.to_string(), "2251.00");
    assert_eq!(total.normalize().mantissa(), 2251);
    assert_eq!(total.serialize()[2], 2);
    let exact = Decimal::from_str_exact("2_251.00").unwrap();
    assert_eq!(exact, total);
    assert_eq!(hash_of(&exact), hash_of(&total.normalize()));
}
