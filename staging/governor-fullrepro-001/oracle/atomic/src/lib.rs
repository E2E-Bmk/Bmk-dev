// Oracle atomic tests for the GCRA rate-limiting engine
#![cfg(test)]
#![allow(clippy::all)]

use governor::clock::{Clock, FakeRelativeClock, MonotonicClock, Reference, SystemClock};
use governor::middleware::StateInformationMiddleware;
use governor::nanos::Nanos;
use governor::state::keyed::HashMapStateStore;
use governor::{
    DefaultDirectRateLimiter, DefaultKeyedRateLimiter, InsufficientCapacity, Quota, RateLimiter,
};
use nonzero_ext::nonzero;
use std::time::Duration;

fn ms(n: u64) -> Duration {
    Duration::from_millis(n)
}

fn ns(n: u64) -> Duration {
    Duration::from_nanos(n)
}

include!("parts/quota.rs");
include!("parts/direct.rs");
include!("parts/notuntil.rs");
include!("parts/keyed.rs");
include!("parts/clock.rs");
include!("parts/middleware.rs");
