// Oracle integration tests: each test chains at least three projections of
// the stored decision state (quota arithmetic -> decisions -> denial
// interrogation / snapshots / housekeeping).
#![cfg(test)]
#![allow(clippy::all)]

use governor::clock::{Clock, FakeRelativeClock};
use governor::middleware::StateInformationMiddleware;
use governor::nanos::Nanos;
use governor::{InsufficientCapacity, Quota, RateLimiter};
use nonzero_ext::nonzero;
use std::time::Duration;

fn ms(n: u64) -> Duration {
    Duration::from_millis(n)
}

fn ns(n: u64) -> Duration {
    Duration::from_nanos(n)
}

mod gateway {
    use super::*;
    include!("all/gateway.rs");
}
mod tenants {
    use super::*;
    include!("all/tenants.rs");
}
mod observability {
    use super::*;
    include!("all/observability.rs");
}
mod scheduling {
    use super::*;
    include!("all/scheduling.rs");
}
