// Oracle integration tests: each test chains at least three projections of
// the packed decimal value (parse/construct -> arithmetic -> scale surgery ->
// render/introspect/convert).
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

mod billing {
    use super::*;
    include!("all/billing.rs");
}
mod canonical {
    use super::*;
    include!("all/canonical.rs");
}
mod precision {
    use super::*;
    include!("all/precision.rs");
}
mod conversion_flow {
    use super::*;
    include!("all/conversion_flow.rs");
}
