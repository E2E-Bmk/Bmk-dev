// Oracle atomic tests for the decimal arithmetic engine
#![cfg(test)]
#![allow(clippy::all)]

use rust_decimal::prelude::*;
use rust_decimal::Error;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

fn d(s: &str) -> Decimal {
    Decimal::from_str(s).unwrap()
}

fn hash_of(value: &Decimal) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn panics<F: FnOnce() -> Decimal + std::panic::UnwindSafe>(f: F) -> bool {
    std::panic::catch_unwind(f).is_err()
}

include!("parts/construction.rs");
include!("parts/parsing.rs");
include!("parts/rendering.rs");
include!("parts/arithmetic.rs");
include!("parts/rounding.rs");
include!("parts/conversion.rs");
