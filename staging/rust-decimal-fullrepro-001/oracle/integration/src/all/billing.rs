// Billing-style flows: parse -> exact arithmetic under the scale laws ->
// presentation-edge rounding -> rendering.

#[test]
fn generated_invoice_scale_flow() {
    let unit_price = d("24.95");
    let quantity = Decimal::from(3u32);
    let discount = d("0.075");

    let gross = unit_price * quantity;
    assert_eq!(gross.to_string(), "74.85");
    assert_eq!(gross.scale(), 2);

    let rebate = gross * discount;
    assert_eq!(rebate.to_string(), "5.61375");
    assert_eq!(rebate.scale(), 5);

    let net = gross - rebate;
    assert_eq!(net.to_string(), "69.23625");
    assert_eq!(net.scale(), 5);

    let payable = net.round_dp(2);
    assert_eq!(payable.to_string(), "69.24");
    assert_eq!(payable.scale(), 2);
    // format precision truncates toward zero, unlike round_dp's banker's rounding
    assert_eq!(format!("{:.2}", net), "69.23");
}

#[test]
fn generated_tax_ladder_with_strategies() {
    let base = d("199.99");
    let rate = d("0.0825");
    let tax = base * rate;
    assert_eq!(tax.to_string(), "16.499175");
    assert_eq!(tax.scale(), 6);

    let up = tax.round_dp_with_strategy(2, RoundingStrategy::AwayFromZero);
    let down = tax.round_dp_with_strategy(2, RoundingStrategy::ToZero);
    let bankers = tax.round_dp(2);
    assert_eq!(up.to_string(), "16.50");
    assert_eq!(down.to_string(), "16.49");
    assert_eq!(bankers.to_string(), "16.50");

    let total = base + up;
    assert_eq!(total.to_string(), "216.49");
    assert_eq!(total.scale(), 2);
    assert!(total.to_f64().unwrap() > 216.0);
}

#[test]
fn generated_ledger_sum_then_split() {
    let entries = [d("10.05"), d("20.10"), d("30.15"), d("-5.30")];
    let total: Decimal = entries.iter().sum();
    assert_eq!(total.to_string(), "55.00");
    assert_eq!(total.scale(), 2);

    let per_share = total / d("3");
    assert_eq!(per_share, d("18.333333333333333333333333333"));

    let cents = per_share.round_dp(2);
    assert_eq!(cents.to_string(), "18.33");
    let remainder = total - cents * d("3");
    assert_eq!(remainder.to_string(), "0.01");
    assert!(remainder > Decimal::ZERO);
    assert_eq!(remainder.mantissa(), 1);
    assert_eq!(remainder.scale(), 2);
}

#[test]
fn generated_running_balance_with_checked_guards() {
    let mut balance = d("100.00");
    let debits = [d("12.75"), d("0.05"), d("87.20")];
    for debit in debits {
        balance = balance.checked_sub(debit).unwrap();
    }
    assert_eq!(balance.to_string(), "0.00");
    assert!(balance.is_zero());
    assert!(balance.is_integer());
    assert_eq!(balance.normalize().scale(), 0);
    assert_eq!(balance.checked_div(Decimal::ZERO), None);
    let restored = balance.checked_add(d("42.424242")).unwrap();
    assert_eq!(restored.round_sf(3), Some(d("42.4")));
}

#[test]
fn generated_unit_price_backout_via_rem() {
    let paid = d("107.50");
    let unit = d("12.50");
    let leftover = paid % unit;
    assert_eq!(leftover.to_string(), "7.50");
    let whole_units = ((paid - leftover) / unit).normalize();
    assert_eq!(whole_units.to_string(), "8");
    assert!(whole_units.is_integer());
    assert_eq!(whole_units.to_u32(), Some(8));
    assert_eq!(whole_units * unit + leftover, paid);
}

#[test]
fn generated_percentage_change_report() {
    let old_value = d("64.00");
    let new_value = d("72.32");
    let change = (new_value - old_value) / old_value * Decimal::ONE_HUNDRED;
    assert_eq!(change.normalize().to_string(), "13");
    assert_eq!(format!("{:.1}", change), "13.0");
    assert!(change.is_integer());
    let as_fraction = change / Decimal::ONE_HUNDRED;
    assert_eq!(as_fraction.normalize(), d("0.13"));
    assert_eq!(as_fraction.to_f64(), Some(0.13));
}
