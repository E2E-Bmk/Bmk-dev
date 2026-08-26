// Canonical-form flows: equality/hash across scale representations,
// normalize as the canonical image, serialize as the byte image.

#[test]
fn generated_aggregation_canonical_form() {
    let entries = [d("1.50"), d("2.25"), d("-0.75")];
    let total: Decimal = entries.iter().sum();
    assert_eq!(total.to_string(), "3.00");
    assert_eq!(total.scale(), 2);

    let canonical = total.normalize();
    assert_eq!(canonical.to_string(), "3");
    assert_eq!(canonical.scale(), 0);
    assert_eq!(total, canonical);
    assert_eq!(hash_of(&total), hash_of(&canonical));

    let bytes = total.serialize();
    assert_eq!(bytes[2], 2);
    assert_eq!(Decimal::deserialize(bytes), total);
    assert_eq!(Decimal::deserialize(bytes).scale(), 2);
}

#[test]
fn generated_scale_representations_one_bucket() {
    use std::collections::HashMap;
    let mut occurrences: HashMap<Decimal, u32> = HashMap::new();
    for input in ["2.5", "2.50", "2.500", "02.5000"] {
        *occurrences.entry(d(input)).or_insert(0) += 1;
    }
    assert_eq!(occurrences.len(), 1);
    assert_eq!(occurrences[&d("2.5")], 4);

    let arithmetic_image = d("5") / d("2");
    assert_eq!(arithmetic_image, d("2.5"));
    assert!(occurrences.contains_key(&arithmetic_image));
}

#[test]
fn generated_negative_zero_pipeline() {
    let mut negative_zero = d("0.00");
    negative_zero.set_sign_negative(true);
    assert!(negative_zero.is_sign_negative());
    assert!(negative_zero.is_zero());
    assert_eq!(negative_zero, Decimal::ZERO);
    assert_eq!(negative_zero.to_string(), "-0.00");

    let bytes = negative_zero.serialize();
    assert_eq!(bytes[3], 128);
    assert_eq!(bytes[2], 2);
    let back = Decimal::deserialize(bytes);
    assert!(back.is_sign_negative());
    assert_eq!(back.to_string(), "-0.00");

    let canonical = negative_zero.normalize();
    assert!(canonical.is_sign_positive());
    assert_eq!(canonical.serialize(), [0u8; 16]);
    assert_eq!(canonical.to_string(), "0");
}

#[test]
fn generated_sort_stability_across_scales() {
    let mut values = vec![d("1.10"), d("1.2"), d("1.1"), d("0.9"), d("1.20")];
    values.sort();
    assert_eq!(values[0].to_string(), "0.9");
    assert_eq!(values[1], d("1.1"));
    assert_eq!(values[2], d("1.1"));
    assert_eq!(values[3], d("1.2"));
    assert_eq!(values[4], d("1.2"));
    let max = values.iter().copied().max().unwrap();
    let min = values.iter().copied().min().unwrap();
    assert_eq!(max, d("1.2"));
    assert_eq!(min.to_string(), "0.9");
    // Iterator::max returns the last maximal element (the scale-2 image),
    // and subtraction keeps the larger operand scale.
    assert_eq!((max - min).to_string(), "0.30");
}

#[test]
fn generated_display_distinguishes_what_eq_conflates() {
    let coarse = d("5.1");
    let fine = d("5.100");
    assert_eq!(coarse, fine);
    assert_eq!(hash_of(&coarse), hash_of(&fine));
    assert_ne!(coarse.to_string(), fine.to_string());
    assert_ne!(coarse.scale(), fine.scale());
    assert_ne!(coarse.mantissa(), fine.mantissa());
    assert_eq!(coarse.mantissa() * 100, fine.mantissa());
    assert_eq!(fine.normalize().mantissa(), coarse.mantissa());
}

#[test]
fn generated_byte_image_survives_arithmetic_identity() {
    let value = d("-31.0075");
    let identity = value + Decimal::ZERO;
    assert_eq!(identity.scale(), 4);
    assert_eq!(identity, value);
    let restored = Decimal::deserialize(identity.serialize());
    assert_eq!(restored.mantissa(), -310075);
    assert_eq!(restored.scale(), 4);
    assert_eq!(restored.to_string(), "-31.0075");
    assert_eq!(restored.abs().serialize()[3], 0);
}
