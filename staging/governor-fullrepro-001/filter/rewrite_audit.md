# Rewrite audit — governor-fullrepro-001

Upstream test surface at 0.9.0 (commit pinned in task.json): eleven
integration test files under `governor/tests/` (51 `#[test]`/async test fns)
plus in-src `#[cfg(test)]` modules (~24 fns) covering gcra internals, quota
getters, nanos arithmetic, and clock trait plumbing.

Decision: **generated_only** oracle. Every upstream file is discarded as a
carrier; the deterministic behavioral intents are re-expressed as freshly
authored tests with fresh quota values, key names, and clock-advance
schedules, expected values verified by running the pinned reference (probe
binary, two rounds, then full-suite reference runs).

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| tests/direct.rs | 11 | discard, re-express | 8 of 11 are deterministic public-API FakeRelativeClock scenarios (first-cell, burst deny, issue-107 no-extra-cell, check_n equivalence, batch capacity, wait-time loop) — intents kept and re-expressed with fresh quotas/advances; `actual_threadsafety` needs `crossbeam` scoped threads (scheduling-dependent), `stresstest_large_quotas` is a perf/thread stress, `default_direct` reduced to the clock-independent first-check fact the spec states |
| tests/keyed_hashmap.rs | 6 | discard, re-express | first-cell, burst deny, `expiration` (retain_recent thresholds via into_state_store), `hashmap_length`, `hashmap_shrink_to_fit` re-expressed with fresh keys/offsets; `actual_threadsafety` discarded (crossbeam) |
| tests/keyed_dashmap.rs | 6 | discard, re-express | same intents on the concurrent store; re-expressed as store-parity assertions |
| tests/keyed.rs | 1 | discard, re-express | generic keyed smoke — covered by keyed part |
| tests/middleware.rs | 5 | discard, re-express | `changes_allowed_type` (custom `RateLimitingMiddleware` impl — public trait, spec-declared) and the snapshot-tracking tests re-expressed with fresh quotas; `mymw_derives` asserts Debug of a test-local type (not library behavior); real-clock variant reduced to clock-independent facts |
| tests/custom_hashers.rs | 8 | discard, re-express | hasher plumbing via std `BuildHasher` — public surface; re-expressed with one fresh custom hasher exercised on both store families |
| tests/memory_leaks.rs | 4 | discard | leak counting via allocator instrumentation — not a spec behavior |
| tests/proptests.rs | 2 | discard | `proptest` dependency; randomized inputs are not reproducible oracle material |
| tests/future.rs | 11 | discard | async `until_ready`/jitter surface — excluded by Non-Goals |
| tests/sinks.rs | 2 | discard | futures sink combinators — excluded by Non-Goals |
| tests/streams.rs | 1 | discard | futures stream combinators — excluded by Non-Goals |
| in-src `#[cfg(test)]` | ~24 | discard, re-express | gcra/nanos/quota unit tests drive internals (`Gcra::new`, private fields); public intents (quota getter arithmetic, nanos conversions, clock trait laws) re-expressed through the declared import surface |

functions_in_scope: 51 integration-test fns; ~24 in-src fns audited for
intent only.

## Fresh-vocabulary policy

Every generated test uses freshly chosen burst sizes, periods, key strings,
and advance schedules not present in upstream tests (upstream: bursts
2/4/5/20 with 1ms steps and keys `foo/bar/baz`; oracle: bursts 3/4/6/7 with
distinct step patterns and domain-flavored keys). Boundary constants that
admit only one interesting value (nanosecond truncation of 1e9/3, the
`Nanos(...)` debug wrapper, the fixed Display sentences) are shared by
necessity and were probe-verified against the reference, not copied from
test expectations.

## Dummy-gate policy (static audit)

A stub crate whose public functions all `unimplemented!()` panics on first
call. Every generated test constructs a `Quota` and a limiter and asserts
produced decision values (or asserts `None`/`Err` values produced by the
reference), so all tests fail against such a stub. No `#[should_panic]`
tests are used; the one panic contract in the spec (clock overflow) is not
asserted in the oracle.
