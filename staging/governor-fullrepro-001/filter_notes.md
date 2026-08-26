# Stage 1 screening — governor-fullrepro-001

repo: boinkor-net/governor
source_path: https://github.com/boinkor-net/governor (local clone /tmp/refs/governor)
commit: e850a9d7ec3840fce5f15c0909ab844332944560 (tag v0.9.0, released 2025-03-24)
src_loc: 3687 in governor/src (incl. ~350 lines of in-src #[cfg(test)] modules;
~3300 non-test), split across gcra.rs (GCRA core), quota.rs, nanos.rs (u64
nanosecond arithmetic with saturating conversions), clock.rs + clock/
(Clock/Reference traits, FakeRelativeClock, MonotonicClock, SystemClock,
QuantaClock), state.rs + state/{direct,keyed,in_memory} (atomic CAS state
stores, direct + two keyed maps), middleware.rs (outcome-projection hooks),
errors.rs, jitter.rs
test_functions: 75 — 51 in tests/ (direct 12, future 11, keyed_dashmap 7,
keyed_hashmap 7, middleware 5+2 doc-shaped, custom_hashers 8, memory_leaks 7,
sinks 3, streams 1, proptests 2 property blocks), 24 in-src unit tests
test_files: tests/{direct,keyed,keyed_dashmap,keyed_hashmap,middleware,
custom_hashers,future,sinks,streams,memory_leaks,proptests}.rs + in-src
#[cfg(test)] modules
dominant_test_styles: behavioral unit tests over the public RateLimiter API
driven by FakeRelativeClock advances (deterministic); a few async
timing-window tests; two proptest blocks
public_docs: docs.rs/governor 0.9.0 (crate root, module `_guide` user's guide
with quota/clock/keyed/middleware walkthroughs, full rustdoc for
Quota/RateLimiter/NotUntil/StateSnapshot/clock module with per-method examples
and None/Err contracts), README.md
core_fact_source: one GCRA (generic cell rate algorithm) state per limiter (or
per key): a theoretical-arrival-time value measured in nanoseconds since the
limiter's start, advanced by a quota-derived emission interval `t` and judged
against tolerance `tau = t * burst`. Every public surface is a projection of
that single value and the quota parameters.
derived_views: (1) quota construction — per_second/per_minute/per_hour,
with_period + allow_burst, deprecated new, getters replenish_interval/
burst_size/burst_size_replenished_in (nanosecond division laws); (2) direct
decisions — check() / check_n() returning Ok or NotUntil (wait_time_from,
earliest_possible, quota round-trip) and InsufficientCapacity for n > burst;
(3) keyed decisions — check_key/check_key_n over HashMap and DashMap stores
plus store hygiene (retain_recent, shrink_to_fit, len, is_empty); (4)
middleware — NoOpMiddleware unit positive outcome vs StateInformationMiddleware
StateSnapshot (quota reconstruction from GCRA parameters,
remaining_burst_capacity evolution); (5) clock abstraction —
FakeRelativeClock::advance drives all of the above deterministically;
direct_with_clock/new generic constructors; into_state_store/clock accessors
external_deps: nonzero_ext, parking_lot, spinning_top, portable-atomic,
smallvec, hashbrown 0.15, cfg-if, web-time (all no-I/O); optional dashmap
(keyed store, in scope), quanta (TSC clock — constructors exist but oracle
drives only FakeRelativeClock), rand/getrandom (jitter — scoped out),
futures-* (async wait surface — scoped out)
test_import_audit: clean — every tests/ file imports only
governor::{Quota, RateLimiter, Jitter, clock::*, middleware::*, prelude::*}
plus nonzero_ext/futures_executor/assertables dev-deps; no private modules,
no test-support carriers
docs_test_alignment: aligned — the rustdoc guide and per-method docs cover the
same decision/snapshot/keyed projections the tests exercise
contamination_note: governor@0.9.0, released 2025-03-24, likely before or near
current model training cutoffs; GCRA is a published algorithm and the crate is
popular, so the oracle asserts freshly chosen quota/advance matrices
probe-verified against the pinned reference rather than upstream fixture
values
decision: keep
reason: a rate-decision rule engine whose entire observable contract is GCRA
arithmetic over one theoretical-arrival-time value — burst windows, emission
intervals with integer-nanosecond truncation, wait-time computation, snapshot
reconstruction — projected through ≥5 public surfaces and driven by a
deterministic fake clock.
risks: (a) async wait/stream/sink surfaces are real-time bound — excluded via
Non-Goals, sync core retains ≥5 projections; (b) jitter uses rand — scoped
out; (c) QuantaClock is hardware-dependent — only clock-independent assertions
(first-cell conformance) touch default constructors, all timing math runs on
FakeRelativeClock; (d) DashMap iteration order — no order-sensitive
assertions; (e) integer-nanosecond truncation in per_second(3) etc. must be
probe-verified (333333333ns not 1/3s).
scope_plan: N/A (3687 LOC, 75 test functions)

Difficulty shapes (selection rationale): reimplementation of an algorithmic
rule rather than a call into it (GCRA theoretical-arrival-time update with
burst tolerance, nanosecond-integer emission intervals, saturating Nanos
arithmetic); integration tests spanning ≥3 projections (quota → keyed check
→ NotUntil wait math → snapshot burst capacity → store retention over one
clock timeline); multi-component collaboration (Quota + Clock + state store +
middleware cooperate in every scenario — a one-line demo is impossible).
