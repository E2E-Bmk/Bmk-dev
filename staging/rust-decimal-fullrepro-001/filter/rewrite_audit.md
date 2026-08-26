# Rewrite audit — rust-decimal-fullrepro-001

Upstream test surface at 1.42.1 (c7efe16): one large public-API integration
file (`tests/decimal_tests.rs`, 173 `#[test]` fns), three feature-gated test
files, generated DB-driver tests, and in-src `#[cfg(test)]` modules.

Decision: **generated_only** oracle. Every upstream file is discarded as a
carrier; behavioral intents are re-expressed as freshly authored tests with
fresh operand/scale matrices, expected values verified by running the pinned
reference (probe binary, three rounds, then full-suite reference runs).

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| tests/decimal_tests.rs | 173 | discard, re-express | public-API-only but unusable as a carrier: `mod macros;` drags a helper module shared with the feature-gated macro tests; many fns are `#[cfg(feature = ...)]` (maths, legacy-ops, c-repr, align16); several import `num_traits::Inv` and `num_traits::Signed` directly rather than through the prelude surface the spec declares; the table-driven fns bundle dozens of loosely related assertions (one fn walks parsing, arithmetic, and rendering in one loop), which defeats per-behavior scoring; operand tables are verbatim upstream values — memorization-prone. Intents kept as a checklist: mantissa/scale extraction, parse/render round trips, scale-law arithmetic, rounding-strategy matrix, significant-figure rounding, rescale/normalize, checked/saturating families, primitive conversions, serialize bytes, error paths |
| tests/macros.rs | 2 | discard | `macros` feature (compile-time literal macro) — out of scope per Non-Goals |
| tests/version-numbers.rs | 2 | discard | crate-metadata self-checks (README version sync) — not a library behavior |
| tests/wasm.rs | 1 | discard | wasm32 target only |
| tests/generated/* | — | discard | DB-driver test matrix generated for postgres/diesel features — out of scope |
| src/str.rs `#[cfg(test)]` | 35 | discard, re-express | drives the private parser internals (`parse_str_radix_10` variants) directly; behavioral intents (rounding vs exact at digit 29, underscore placement, error taxonomy) re-expressed through public `FromStr`/`from_str_exact`/`from_str_radix` |
| src/serde.rs, src/rand*.rs, src/mysql.rs, src/ops/array.rs, src/maths.rs, src/proptest.rs, src/fuzz.rs tests | 40 | discard | feature-gated surfaces excluded by the spec's Non-Goals |
| src/decimal.rs, src/arithmetic_impls.rs, src/ops/legacy.rs tests | 4 | discard | internal invariant checks (`unpack` round trips, legacy-ops parity) on private surface |

functions_in_scope: 213 (173 decimal_tests + 35 str.rs + 2 macros + 2
version-numbers + 1 wasm; feature-gated in-src modules not compiled in the
default configuration are listed for completeness but carry no in-scope
public behavior beyond what decimal_tests already exercises)

## Fresh-vocabulary policy

Every generated test uses freshly chosen operand values, scale combinations,
and corpus strings not present in `tests/decimal_tests.rs`; the handful of
boundary constants that admit only one interesting value (`MAX`, `MIN`,
`2^96-1` digit strings, the 28-digit scale cap, documented rustdoc examples
like `from_parts(1,2,3,false,4)`) are shared with upstream by necessity and
were probe-verified against the reference rather than copied from test
expectations.

## Dummy-gate policy (static audit)

A stub crate whose public functions all `unimplemented!()` panics on first
call. Every generated test calls into `rust_decimal` and asserts a produced
value (or asserts an `Err`/`None` value produced by the reference), so all
tests fail against such a stub. No `#[should_panic]` tests are used: panic
contracts are asserted through `std::panic::catch_unwind` and every such test
also asserts at least one produced value in the same test body, so a
panic-everywhere stub still fails it.
