# Stage 1 screening — rust-decimal-fullrepro-001

repo: paupino/rust-decimal
source_path: https://github.com/paupino/rust-decimal (local clone /tmp/refs/rust-decimal)
commit: c7efe1690bd8e460731ff97a7c4941ecffc8751b (tag 1.42.1, released 2026-06-11)
src_loc: 12006 total src/; 8838 in the always-compiled core (lib.rs, decimal.rs,
constants.rs, error.rs, str.rs, arithmetic_impls.rs, ops.rs, ops/*) — the rest is
feature-gated (serde, db backends, maths, rand, rkyv, fuzz, wasm) and out of
scope
test_functions: 250 `#[test]` total — 173 in tests/decimal_tests.rs (public-API
table-driven), 35 in-src in str.rs (internal parser paths), the rest split
across feature-gated modules (serde 22, rand 8, mysql 3, ops/array 2, ...)
test_files: tests/{decimal_tests.rs, macros.rs, version-numbers.rs, wasm.rs,
generated/} + in-src #[cfg(test)] modules
dominant_test_styles: table-driven behavioral unit tests over the public
Decimal API (parse → op → to_string round trips); feature-matrix smoke tests
public_docs: docs.rs/rust_decimal 1.42.1 (crate root guide + full rustdoc for
Decimal/Error/RoundingStrategy with per-method examples and panic/None
contracts), README.md (feature table, usage examples, string/float conversion
guidance, rounding-strategy table)
core_fact_source: one 128-bit packed value — a 96-bit unsigned integer
mantissa, a sign flag, and a scale in 0..=28 (m / 10^e). Every public surface
is a projection of that triple and of the documented scale/rounding laws over
it.
derived_views: (1) construction — new/try_new (i64+scale),
from_i128_with_scale/try_, from_parts (32-bit limbs), From<ints>,
try_from f32/f64 (and *_retain), from_scientific, FromStr (with rounding at 28
fractional digits) vs from_str_exact (Underflow instead), from_str_radix;
(2) arithmetic — +,-,*,/,% with documented result-scale laws, panics on
overflow, plus checked_/saturating_ families projecting the same facts as
Option/saturation; (3) scale surgery — round, round_dp (banker's default),
round_dp_with_strategy (8 documented RoundingStrategy variants), round_sf
family, trunc, trunc_with_scale, floor/ceil, rescale/set_scale, normalize;
(4) rendering — Display preserves the scale as trailing zeros, {:e}
scientific rendering, to_string↔FromStr round trip; (5) introspection &
conversion — scale/mantissa/unpack-free accessors (is_zero, is_sign_negative,
is_integer, abs/signum), num-traits ToPrimitive/FromPrimitive projections,
TryFrom int/float; (6) equivalence — Eq/Ord/Hash agree across distinct
representations of one number (1.0 == 1.00 == normalize()), constants
(ZERO/ONE/TWO/TEN/ONE_HUNDRED/ONE_THOUSAND/PI/E family, MAX/MIN) participate in
every other view
external_deps: arrayvec + num-traits only in scope (both no-I/O, old-stable);
all other dependencies are feature-gated and excluded (serde, diesel,
postgres, rkyv, borsh, rand, ndarray, rocket, macros)
test_import_audit: clean for the retained surface — tests/decimal_tests.rs
imports only rust_decimal::{Decimal, Error, RoundingStrategy} plus num_traits
trait methods documented through the prelude; in-src str.rs tests call private
parser internals (not retainable, behaviors re-expressible through
FromStr/from_str_exact/from_scientific); feature-gated test files are out of
scope
docs_test_alignment: aligned — docs.rs documents the same projections the
tests exercise (per-method examples mirror the table-driven assertions, incl.
result-scale and rounding-strategy tables)
contamination_note: rust_decimal@1.42.1, released 2026-06-11, after the
assumed training cutoff for current models; the crate itself is old and
popular (memorization-prone method names), but the oracle asserts freshly
chosen operand/scale matrices probe-verified against the pinned reference, not
upstream fixture values
decision: keep
reason: a fixed-precision decimal arithmetic engine whose entire contract is a
matrix of library-specific scale-propagation and rounding laws (banker's
rounding default, 28-digit mantissa saturation, scale clamping) — arithmetic
reimplementation plus an equivalence-heavy representation model (equal values
at different scales must agree under Eq/Ord/Hash while Display distinguishes
them), projected through ≥5 public surfaces.
risks: (a) mul/div result-scale behavior on non-representable results is
implementation-defined upstream in edge regions — the spec pins only the
documented laws (truncation to 28 significant digits in div, banker's rounding
on mul overflow of scale) and the oracle probe-verifies every asserted value
against the reference; (b) f64→Decimal conversion dual forms (try_from vs
from_f64_retain) must be described precisely or scoped to documented examples;
(c) popular crate — mitigated with fresh operand matrices; (d) num-traits
prelude re-exports must be enumerated in the spec's Public Interface so the
symbol lint stays meaningful.
scope_plan: N/A (12006 LOC total with 8838 in-scope core; 250 test functions,
173 in the single public-API integration file)

Difficulty shapes (selection rationale): reimplementation of a format/number
rule rather than a call into it (96-bit decimal arithmetic with documented
scale-propagation laws, two-phase string parsing with rounding vs exact modes,
8 rounding strategies); equivalence judgement (Eq/Ord/Hash across scale
representations, normalize() as canonical form, from_str vs from_str_exact
divergence); integration spanning ≥3 projections (parse → checked arithmetic →
round_dp_with_strategy → Display/rescale → mantissa/scale introspection all
over one packed value).
