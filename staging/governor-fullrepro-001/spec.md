<!-- INTERNAL
task_id: governor-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by two probe rounds against
the pinned reference: quota constructor nanosecond-truncation laws
(per_second(3) yields a 333333333ns replenish interval and a 999999999ns
full-burst figure), the deprecated new() division law, the decision laws
(burst-budget conformance, deny boundary, exact-boundary conformance, batch
weight math and the InsufficientCapacity carrier holding the capacity),
NotUntil absolute-instant projection with a pre-advanced clock (earliest is
start-relative + limiter start), wait_time_from clamping to zero,
StateSnapshot remaining-burst-capacity countdown/regain/idle-reset values,
quota reconstruction round trip through snapshots, keyed store housekeeping
retention boundary (a key at exactly the drop threshold is evicted),
per-store len/is_empty/into_state_store behavior, FakeRelativeClock shared
clones and equality, NotUntil/InsufficientCapacity Display strings
source_boundary: docs.rs/governor 0.9.0 (crate root, _guide module, clock,
middleware, state, state::keyed, nanos module docs and per-method examples),
README.md; reference behavior observed by running the pinned checkout
(probe binary, two rounds). The async wait/stream/sink surface (until_ready,
until_key_ready, RatelimitedStream, RatelimitedSink, prelude extension
traits), Jitter, QuantaUpkeepClock, and the no_std configuration are
excluded from scope.
-->

# governor Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`governor` is a rate-limiting library built around a continuous-time cell
admission rule. A rate limiter is configured with a `Quota` — a maximum
burst size and a replenish interval — and answers one question: is a cell
(a request, a packet, an action) allowed right now? Decisions are made
against a single stored value per limiter (or per key in a keyed limiter):
the time at which the next cell is theoretically expected. Because the
whole state is one time value, decisions are lock-free in the direct case
and cheap in the keyed case, and the same arithmetic yields precise
answers to "when is the next cell allowed?" without any background timer
or token-refill thread.

The library separates four concerns that cooperate in every decision: the
`Quota` (how many cells per what period), the clock (a pluggable time
source, including a manually advanced test clock), the state store (one
direct slot, or a map from keys to slots), and the middleware (what data a
decision returns beyond yes/no). Callers combine these through the
`RateLimiter` type, which exposes direct check methods, keyed check
methods, and store housekeeping.

The installable crate name is `governor`.

## Non-Goals

- This specification does not require the asynchronous waiting surface:
  no `until_ready`, `until_ready_with_jitter`, `until_key_ready`,
  stream or sink adaptors, or the `prelude` extension traits.
- This specification does not require randomized retry jitter: the
  `Jitter` type and jitter-accepting methods are not part of the
  described surface.
- This specification does not require hardware-timestamp clock upkeep
  (`QuantaUpkeepClock`) or any accuracy guarantee of the real-time
  clocks beyond monotonicity; timing-law assertions are made against the
  manually advanced test clock.
- This specification does not require a `no_std` build configuration.
- This specification does not define persistence of rate-limiting state
  across process restarts.
- This specification does not define eviction policies beyond the
  documented `retain_recent` rule.

## Representative Workflows

Two workflows illustrate how quotas, clocks, decisions, and snapshots
cooperate.

**Direct limiter with a test clock.** A limiter admits a burst, denies the
next cell with a precise wait time, and admits again once the clock
advances:

```rust
use governor::clock::{Clock, FakeRelativeClock};
use governor::{Quota, RateLimiter};
use nonzero_ext::nonzero;
use std::time::Duration;

let clock = FakeRelativeClock::default();
let limiter = RateLimiter::direct_with_clock(
    Quota::per_second(nonzero!(5u32)),
    clock.clone(),
);

for _ in 0..5 {
    assert!(limiter.check().is_ok());       // the full burst conforms
}
let denied = limiter.check().unwrap_err();  // the sixth cell does not
assert_eq!(
    denied.wait_time_from(clock.now()),
    Duration::from_millis(200),             // one replenish interval
);

clock.advance(Duration::from_millis(200));
assert!(limiter.check().is_ok());           // exactly one cell regained
```

**Keyed API budget with snapshots and housekeeping.** A keyed limiter
tracks one budget per client, reports remaining capacity through a
middleware, and evicts idle keys:

```rust
use governor::clock::FakeRelativeClock;
use governor::middleware::StateInformationMiddleware;
use governor::{Quota, RateLimiter};
use nonzero_ext::nonzero;
use std::time::Duration;

let clock = FakeRelativeClock::default();
let limiter = RateLimiter::hashmap_with_clock(
    Quota::per_second(nonzero!(3u32)),
    clock.clone(),
).with_middleware::<StateInformationMiddleware>();

let snapshot = limiter.check_key(&"client-a").unwrap();
assert_eq!(snapshot.remaining_burst_capacity(), 2);

assert!(limiter.check_key(&"client-b").is_ok());
assert_eq!(limiter.len(), 2);               // two live keys

clock.advance(Duration::from_secs(60));
limiter.retain_recent();                    // both keys are stale now
assert!(limiter.is_empty());
```

## Quotas and Time Arithmetic

This section defines how a rate is expressed and which exact durations a
quota reports. All quota arithmetic is integer nanosecond arithmetic;
divisions truncate.

**Constructors.** `Quota::per_second(max_burst)`,
`Quota::per_minute(max_burst)`, and `Quota::per_hour(max_burst)` each take
a nonzero 32-bit burst count and produce a quota whose replenish interval
is the period (1, 60, or 3600 seconds, in nanoseconds) divided by
`max_burst`, truncated to whole nanoseconds: a per-second quota of 3 cells
replenishes one cell every `333333333` nanoseconds, and a per-minute quota
of 7 cells every `8571428571` nanoseconds. The given burst count is also
the maximum burst size. `Quota::with_period(replenish_1_per)` returns a
quota that replenishes one cell per the given interval with a burst size
of one, wrapped in `Some`; WHEN the interval is zero THEN it returns
`None`. `allow_burst(max_burst)` returns the same quota with only the
burst size replaced. The deprecated constructor
`Quota::new(max_burst, replenish_all_per)` divides the period by the burst
size to obtain the per-cell interval (`new` with a burst of 4 over 2
seconds replenishes one cell per 500 milliseconds) and returns `None` for
a zero period.

**Introspection.** `replenish_interval()` returns the per-cell interval as
a `Duration`. `burst_size()` returns the nonzero burst count.
`burst_size_replenished_in()` returns the per-cell interval multiplied by
the burst count — for `per_second(3)` this is `999999999` nanoseconds, not
one second, because the truncated interval is what multiplies out.

**Equality and rendering.** `Quota` is `Copy`, `Clone`, `Debug`,
`PartialEq`, and `Eq`; two quotas are equal exactly when their burst size
and replenish interval both match. The `Debug` form renders both fields,
as in `Quota { max_burst: 3, replenish_1_per: 333.333333ms }`.

## Rate-Limiting Decisions

This section defines the decision rule every check method applies. One
stored value drives everything: the theoretical arrival time ("TAT") of
the next cell, measured as a duration since the limiter's start instant.

**Decision state and parameters.** At construction the limiter captures
the clock's current instant as its start reference. A quota translates to
two derived durations: the per-cell interval `t` (the replenish interval,
raised to at least one nanosecond), and the burst tolerance
`tau = t × (burst_size − 1)`. A limiter whose state is unset behaves as if
its TAT equals the current measurement instant.

**Single-cell rule.** WHEN `check()` is called at relative time `now`
THEN the cell conforms exactly when `now ≥ TAT − tau` (a measurement at
exactly the boundary conforms); on a conforming decision the stored TAT
becomes `max(TAT, now) + t`. A fresh limiter therefore admits exactly
`burst_size` back-to-back cells at one instant, and afterwards regains one
admissible cell each time the clock advances by `t`. If the cell does not
conform, then `check` must return `Err` carrying a `NotUntil` value and
leave the stored state unchanged.

**Batch rule.** `check_n(n)` admits all `n` cells together or none. The
batch carries additional weight `w = t × (n − 1)`. If `w > tau`, then the
batch can never conform under this quota and `check_n` must return
`Err(InsufficientCapacity(c))` without consulting or modifying the state,
where `c` is the bucket capacity `1 + tau/t` (the burst size). Otherwise
the result is `Ok` wrapping an inner decision: WHEN
`now ≥ (TAT + w) − tau` THEN the batch conforms and the stored TAT becomes
`max(TAT, now) + t × n`; otherwise the inner value is `Err(NotUntil)` and
the state is unchanged. A batch of one behaves exactly like `check`. A
conforming batch equal to the full burst size drains the limiter
completely; a subsequent batch of the same size conforms again after the
clock advances by the full `burst_size_replenished_in` figure.

**The negative outcome.** A `NotUntil` value reports when the denied cell
could conform. `earliest_possible()` returns an absolute clock instant:
the limiter's start reference plus the relative earliest conforming time
(`TAT − tau` for single cells, `(TAT + w) − tau` for batches).
`wait_time_from(from)` returns `earliest_possible` minus `from` as a
`Duration`, clamped to zero WHEN `from` is at or past the earliest
instant. `quota()` returns the exact `Quota` the limiter was built with.
The `Display` form is the fixed sentence `rate-limited until {instant}`
where the instant renders in its `Debug` form (with the test clock:
`rate-limited until Nanos(200ms)`). `NotUntil` values are `Debug`,
`PartialEq`, and `Eq`.

**Capacity failure.** `InsufficientCapacity` is a tuple struct whose
public `u32` field is the maximum number of cells that could ever conform
in one batch. It is `Copy`, `Clone`, `Debug`, `PartialEq`, `Eq`,
implements the standard error trait, and its `Display` form is
`required number of cells {capacity} exceeds bucket's capacity` — the
number shown is the capacity carried in the value.

**Construction of direct limiters.** `RateLimiter::direct(quota)` builds
a direct in-memory limiter on the default real-time clock.
`RateLimiter::direct_with_clock(quota, clock)` accepts any clock
implementation. The most general constructor
`RateLimiter::new(quota, state, clock)` assembles a limiter from an
explicit state store and clock. `with_middleware::<M>()` converts a
limiter to one whose check methods return the middleware's outcome types,
preserving quota, state, start reference, and clock.
`into_state_store()` consumes the limiter and returns the state store;
`clock()` returns a reference to the clock. The alias
`DefaultDirectRateLimiter` names the direct limiter type on the default
clock, and `NotKeyed` is the key type of direct state stores (its only
value is `NotKeyed::NonKey`); `InMemoryState` is the single-slot atomic
store used by direct limiters.

## Keyed Limiters and Store Housekeeping

This section defines limiters that keep one decision state per key and
the operations that manage the key population.

**Keyed checks.** `check_key(&key)` and `check_key_n(&key, n)` apply
exactly the single-cell and batch rules above to the state stored under
`key`; distinct keys are fully independent budgets under one shared quota,
clock, and start reference. A key first seen at relative time `now`
behaves as an unset state (TAT = `now`). The failure paths are the same:
`check_key` returns `Err(NotUntil)`, and `check_key_n` returns
`Err(InsufficientCapacity)` for an impossible batch or `Ok(Err(NotUntil))`
for a currently non-conforming one.

**Stores and constructors.** Two keyed store families exist: a
mutex-guarded standard `HashMap` (`HashMapStateStore<K>`) and a sharded
concurrent map (`DashMapStateStore<K>`); `DefaultKeyedStateStore<K>` is
the concurrent map in the default configuration, and
`DefaultKeyedRateLimiter<K>` names the keyed limiter on that store and the
default clock. `RateLimiter::keyed(quota)` builds on the default store and
real-time clock; `RateLimiter::dashmap(quota)` selects the concurrent map
explicitly; `RateLimiter::hashmap_with_clock(quota, clock)` and
`RateLimiter::dashmap_with_clock(quota, clock)` accept a custom clock;
`hashmap_with_clock_and_hasher(quota, clock, hasher)` and
`dashmap_with_clock_and_hasher(quota, clock, hasher)` additionally accept
a hash-state builder, and `hashmap_with_hasher(quota, hasher)` /
`dashmap_with_hasher(quota, hasher)` do the same on the real-time clock.
A `HashMapStateStore` is constructed directly by wrapping a map value
(`HashMapStateStore::new(...)`), and `into_state_store()` on a keyed
limiter returns the store with its live keys intact. Key types must be
hashable, comparable, and cloneable.

**Population accounting.** `len()` returns the number of keys currently
stored — every key that has ever been checked and not evicted counts,
whether or not its budget is exhausted. `is_empty()` returns whether no
keys are stored. A fresh keyed limiter is empty. WHEN `check_key_n` rejects a batch as
impossible THEN the store must remain unchanged — the capacity test
precedes any state access, so the key is not created.

**Retention.** `retain_recent()` evicts every key whose state is
indistinguishable from a fresh state. The eviction threshold is the
current relative time minus one per-cell interval `t`; a key is retained
exactly when its stored TAT is strictly greater than that threshold. A
key whose TAT equals the threshold is evicted. After eviction a re-check
of an evicted key behaves as a first check. `shrink_to_fit()` reduces the
store's capacity where the store supports it and has no observable effect
on decisions. Both operations, `len`, and `is_empty` exist on both store
families with identical contracts.

## Clocks and Time Sources

This section defines the pluggable time layer every limiter measures
against.

**Traits.** A clock implements `Clock` with an associated `Instant` type
and a `now()` method. An instant implements `Reference`, which requires
`duration_since(earlier)` (saturating: WHEN `earlier` is later THEN the
result is zero) and `saturating_sub(duration)` (WHEN subtraction would
underflow THEN the receiver is returned unchanged), plus addition of a
nanosecond count. `Duration` itself implements `Reference`, and custom
clocks are defined by implementing both traits.

**The nanosecond scalar.** `Nanos` is the crate's u64 nanosecond count,
reachable at `governor::nanos::Nanos`. It converts from and into
`Duration` and `u64` (`Nanos::new(n)`, `as_u64()`), supports saturating
subtraction, and its `Debug` form wraps the equivalent `Duration` debug
rendering, as in `Nanos(200ms)` or `Nanos(1.2s)`. `Nanos` is the instant
type of the test clock, so decision outputs on the test clock render and
compare in `Nanos` values.

**Test clock.** `FakeRelativeClock` is a manually driven clock starting
at zero. `advance(by)` adds a `Duration` to the current reading; `now()`
returns the reading as `Nanos`. Clones share the same underlying reading:
advancing any clone advances them all. Two fake clocks compare equal
exactly when their current readings are equal. The clock never advances
on its own, which makes every decision law in this document exactly
reproducible.

**Real-time clocks.** `MonotonicClock` (the standard monotonic instant)
and `SystemClock` (the wall-clock time) are default-constructible clocks
for production use; `DefaultClock` is the default choice used by the
`direct`/`keyed` constructors. On any real-time clock, a fresh limiter's
first check must conform, and with a burst size of one a second immediate
check must be denied — these hold regardless of clock resolution because
they only require time to be non-negative and far below the replenish
interval of the probing quota.

**Start reference.** Every limiter captures `clock.now()` at construction
as its start. All stored TATs are durations relative to that start;
`NotUntil::earliest_possible` adds them back onto the start to produce an
absolute instant. WHEN a clock is advanced before the limiter is built
THEN the reported earliest instants include that offset (a limiter built
at reading 5s that denies a one-per-second cell reports
`rate-limited until Nanos(6s)`).

## Middleware and State Snapshots

This section defines what a decision returns beyond yes/no, and the
snapshot arithmetic exposed to callers.

**The middleware contract.** A middleware type implements
`RateLimitingMiddleware<P>` for an instant type `P`, choosing a
`PositiveOutcome` type and a `NegativeOutcome` type and providing two
hooks: `allow(key, snapshot)` produces the positive value, and
`disallow(key, snapshot, start)` produces the negative value. Middleware
must not change whether a decision is positive or negative — only what
value each case carries. The middleware is selected per limiter with
`with_middleware::<M>()`.

**Shipped middlewares.** `NoOpMiddleware` (the default) returns the unit
value on conforming decisions and `NotUntil` on denials.
`StateInformationMiddleware` returns a `StateSnapshot` on conforming
decisions and the same `NotUntil` on denials.

**Snapshot arithmetic.** A `StateSnapshot` describes the state *after*
the decision it accompanies. `remaining_burst_capacity()` returns how
many additional cells conform immediately: after the first check on a
fresh limiter with burst size `b` it returns `b − 1`, it counts down by
one per conforming check at one instant, it reaches `0` when the burst is
exhausted, WHEN the clock then advances by exactly one per-cell interval
and one cell is admitted THEN the snapshot returned by that check reports
`0` again (the regained cell was consumed), and WHEN the limiter idles
long enough to fully replenish THEN the next conforming check reports
`b − 1`. `quota()` reconstructs the exact `Quota` the limiter was
configured with — burst size and replenish interval both round-trip
through the snapshot, for constructor-built and `with_period`-derived
quotas alike. Snapshots are `Clone`, `Debug`, `PartialEq`, and `Eq`.
`NotUntil::quota()` performs the same reconstruction on denials.

**Custom middleware.** A caller-defined middleware observes the same
snapshot and start values the shipped ones do; a middleware returning the
unit type in both cases yields check methods whose `Ok` and `Err` both
carry unit values.

## State Model

The library's entire mutable state is a map from keys to one nanosecond
value each (the direct limiter is the special case of a single anonymous
key):

1. **decision state** — the theoretical arrival time per key, advanced
   by `t` per admitted cell (or `t × n` per batch), never mutated by a
   denial;
2. **decision projection** — `check`/`check_n`/`check_key`/`check_key_n`
   return the middleware's positive value or `NotUntil`, whose
   `earliest_possible`/`wait_time_from`/`Display` all derive from the
   same stored value and the limiter's start reference;
3. **capacity projection** — `StateSnapshot::remaining_burst_capacity`
   and `quota` reconstruct burst budget and quota parameters from the
   stored value and the derived `t`/`tau` pair;
4. **population projection** — keyed `len`/`is_empty` count stored keys;
   `retain_recent` evicts by comparing stored values against the
   fresh-state threshold; `into_state_store` hands the raw store back.

The quota, clock, start reference, and middleware selection are fixed at
construction (middleware replaceable via `with_middleware`, which
preserves the rest) and are never mutated by decisions.

## Error Semantics

| Condition | Result |
|---|---|
| Single cell does not conform | `Err(NotUntil)` from `check`/`check_key`; state unchanged |
| Batch weight fits but does not conform now | `Ok(Err(NotUntil))` from `check_n`/`check_key_n`; state unchanged |
| Batch weight `t × (n−1)` exceeds tolerance `tau` | `Err(InsufficientCapacity(capacity))` from `check_n`/`check_key_n`; state untouched |
| `Quota::with_period` or deprecated `Quota::new` with zero period | `None` |
| `FakeRelativeClock::advance` beyond u64 nanoseconds | panic (advancing past ~584 years is unrepresentable) |

`NotUntil` renders as `rate-limited until {instant:?}`;
`InsufficientCapacity` renders as
`required number of cells {capacity} exceeds bucket's capacity` and
implements the standard error trait. Neither type implements conversion
into the other.

## Cross-View Invariants

1. A quota's `burst_size()` must equal both the number of back-to-back
   cells a fresh limiter admits at one instant and the capacity value
   carried by `InsufficientCapacity` for an oversized batch on that
   limiter.
2. `NotUntil::wait_time_from(now)` must equal the exact clock advance
   after which the denied cell conforms: advancing the fake clock by that
   duration and re-checking must return `Ok`, and advancing by one
   nanosecond less must still deny.
3. A snapshot's `quota()` and a denial's `quota()` must both compare
   equal to the `Quota` value the limiter was constructed with, and that
   quota's `replenish_interval()` must equal the observed single-cell
   regain interval on the fake clock.
4. `remaining_burst_capacity()` must equal the number of subsequent
   immediate `check` calls that conform before the first denial, at any
   point in a decision sequence.
5. On a keyed limiter, `len()` must equal the number of distinct keys
   checked since construction (or last eviction), independent of how many
   checks each key received or whether its budget is exhausted; after
   `retain_recent()` it must equal the number of keys whose stored
   arrival time is strictly newer than the fresh-state threshold.
6. Batch and single-cell projections must agree: a conforming
   `check_n(n)` leaves the limiter in exactly the state produced by `n`
   conforming `check` calls at the same instant — subsequent decisions,
   wait times, and snapshots are indistinguishable between the two
   histories.
7. Decisions on the mutex-guarded map store and the concurrent map store
   must be identical for identical key/advance/check sequences.

## Public Interface

### Import Surface

```rust
// crate root
use governor::{Quota, RateLimiter, NotUntil, InsufficientCapacity};
use governor::{DefaultDirectRateLimiter, DefaultKeyedRateLimiter};

// clocks
use governor::clock::{Clock, Reference, FakeRelativeClock,
                      MonotonicClock, SystemClock, DefaultClock};

// nanosecond scalar
use governor::nanos::Nanos;

// middleware
use governor::middleware::{RateLimitingMiddleware, NoOpMiddleware,
                           StateInformationMiddleware, StateSnapshot};

// state stores
use governor::state::{InMemoryState, NotKeyed};
use governor::state::keyed::{HashMapStateStore, DashMapStateStore,
                             DefaultKeyedStateStore};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Quota` | struct | Rate description: burst size + replenish interval |
| `Quota::per_second` / `per_minute` / `per_hour` | fn | Period-divided quota constructors |
| `Quota::with_period` | fn | One-cell-per-interval constructor (`Option`) |
| `Quota::new` | fn | Deprecated burst-over-period constructor (`Option`) |
| `Quota::allow_burst` | fn | Burst-size replacement |
| `Quota::replenish_interval` / `burst_size` / `burst_size_replenished_in` | fn | Quota introspection |
| `RateLimiter` | struct | The limiter tying quota, state, clock, middleware |
| `RateLimiter::direct` / `direct_with_clock` | fn | Direct limiter constructors |
| `RateLimiter::keyed` / `dashmap` / `hashmap_with_hasher` / `dashmap_with_hasher` | fn | Keyed constructors on the default clock |
| `RateLimiter::hashmap_with_clock` / `dashmap_with_clock` | fn | Keyed constructors with custom clock |
| `RateLimiter::hashmap_with_clock_and_hasher` / `dashmap_with_clock_and_hasher` | fn | Keyed constructors with custom clock and hasher |
| `RateLimiter::new` | fn | Generic constructor from quota, store, clock |
| `RateLimiter::check` / `check_n` | fn | Direct decisions |
| `RateLimiter::check_key` / `check_key_n` | fn | Keyed decisions |
| `RateLimiter::retain_recent` / `shrink_to_fit` / `len` / `is_empty` | fn | Keyed store housekeeping |
| `RateLimiter::with_middleware` | fn | Middleware selection |
| `RateLimiter::into_state_store` / `clock` | fn | Component access |
| `NotUntil` | struct | Negative decision: earliest conforming instant |
| `NotUntil::earliest_possible` / `wait_time_from` / `quota` | fn | Denial interrogation |
| `InsufficientCapacity` | struct (tuple) | Batch-can-never-conform error, public `u32` capacity |
| `StateSnapshot` | struct | Post-decision state view |
| `StateSnapshot::remaining_burst_capacity` / `quota` | fn | Snapshot arithmetic |
| `RateLimitingMiddleware` | trait | Decision outcome customization |
| `NoOpMiddleware` | struct | Default unit-outcome middleware |
| `StateInformationMiddleware` | struct | Snapshot-returning middleware |
| `Clock` / `Reference` | trait | Time-source abstraction |
| `FakeRelativeClock` | struct | Manually advanced test clock |
| `MonotonicClock` / `SystemClock` | struct | Real-time clocks |
| `DefaultClock` | type alias | Default clock selection |
| `Nanos` | struct | u64 nanosecond scalar / test-clock instant |
| `InMemoryState` | struct | Single-slot atomic direct store |
| `NotKeyed` | enum | Key type of direct stores (`NonKey`) |
| `HashMapStateStore` / `DashMapStateStore` / `DefaultKeyedStateStore` | type alias | Keyed store families |
| `DefaultDirectRateLimiter` / `DefaultKeyedRateLimiter` | type alias | Default limiter types |

### CLI Entry Points

There is no console script for this crate. Programmatic use is through the
Rust library API.

## Appendix A: Environment

- Language: Rust, edition 2018 or later (toolchain 1.83; the crate's
  declared minimum supported Rust version must not exceed it).
- The crate must build as `governor` with its default configuration
  providing every behavior described here; the assessment suite depends
  on the crate as `governor = { version = "*" }` and additionally uses
  `nonzero_ext` for nonzero literals.
- Both keyed store families (the mutex-guarded standard map and the
  sharded concurrent map) must be available in the default configuration.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Quotas: constructor arithmetic (including nanosecond truncation),
  zero-period rejections, burst replacement, introspection getters,
  equality, and debug rendering.
- Direct decisions: burst admission, deny boundaries (including
  exact-boundary conformance), single-cell regain, batch admission and
  drain, impossible-batch rejection with capacity reporting, and state
  preservation on denials.
- Denial interrogation: earliest instants (including limiters built on
  pre-advanced clocks), wait-time computation and zero clamping, quota
  round trips, and display strings.
- Keyed decisions: per-key independence, first-seen behavior, batch
  variants, both store families, custom hashers, population accounting,
  retention thresholds, and store extraction.
- Clocks: the manually advanced test clock (shared clones, equality,
  readings), reference arithmetic, and the clock-independent facts of
  real-time clocks.
- Middleware: snapshot capacity countdown/regain/idle-reset arithmetic,
  quota reconstruction, the default unit outcome, and caller-defined
  middleware over the trait.

Scoring runs the full test suite against the delivered crate; each test
carries equal weight within its layer. Integration tests combine at least
two behavior domains (for example, keyed decisions plus retention plus
snapshot arithmetic over one clock timeline).
