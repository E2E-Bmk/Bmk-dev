# Rewrite Audit — rrule-fullrepro-001

Upstream commit: fmeringdal/rust-rrule @ 1c3420e356e4a89b1e10ff4ea1ab9cf6da42c3ab
(release v0.14.0), workspace member `rrule`.
Upstream test inventory: 317 test functions — every one an in-crate
`#[cfg(test)]` module under `rrule/src/`; the crate has no external `tests/`
directory at all.

## Why the oracle is generated-only

1. **Every upstream test is in-crate.** The suite lives inside the crate
   (`src/tests/rrule.rs` 173, `src/tests/rfc_tests.rs` 39,
   `src/tests/rruleset.rs` 24, `src/tests/regression.rs` 5,
   `src/tests/serde.rs` 2, `src/tests/daylight_saving.rs` 2,
   `src/tests/datetime.rs` 2, plus ~70 unit tests inside
   `iter/`, `parser/`, `validator/`, and `core/` modules). All import through
   `crate::`/`super::` paths (`use crate::core::Tz`,
   `use crate::tests::common::{test_recurring_rrule, ymd_hms}`) and are
   compiled into the crate itself — structurally unavailable to an external
   oracle that depends on the crate as a registry package.
2. **Shared in-crate helpers are private.** The suite is built on
   `tests/common.rs` helpers (`test_recurring_rrule`, `ymd_hms`,
   `check_occurrences`) that are `pub(crate)`; the unit tests inside
   `parser/`/`validator/` assert on private types (`ContentLineCaptures`,
   internal error constructors) that the spec never declares.
3. **Feature-gated files.** `serde.rs` requires the `serde` feature and
   `regression.rs` partially exercises `exrule`; both features are outside
   the default-feature scope plan.
4. **Anti-memorization.** The upstream fixtures are the classic 1997
   python-dateutil dates (`19970902T090000` etc.) that appear verbatim in
   dateutil, rrule.js, and this crate — maximally memorization-prone. All
   oracle fixtures use fresh 2026–2028 dates, different timezones
   (Denver/Chicago/Tokyo/Paris instead of the upstream's New_York-centric
   set where possible), different property combinations, and different
   assertion angles (getter/Display/stream cross-checks instead of
   occurrence-vector-only checks).

Decision: `oracle_source: generated_only`. Upstream in-crate tests serve as a
behavioral checklist; every oracle test is authored fresh against the spec and
validated by executing the pinned reference.

## Per-file disposition

| file | fns | disposition | reason |
|---|---|---|---|
| src/tests/rrule.rs | 173 | discard, re-express in-scope intent | in-crate (`crate::` imports, pub(crate) helpers); occurrence-stream intent covered by generated iteration/selection tests with fresh dates |
| src/tests/rfc_tests.rs | 39 | discard, re-express in-scope intent | in-crate; RFC parse/iterate intent covered by generated parsing + round-trip tests |
| src/tests/rruleset.rs | 24 | discard, re-express in-scope intent | in-crate; set-algebra intent covered by generated stream/composition tests |
| src/tests/regression.rs | 5 | discard | in-crate; partially exrule-gated (out of scope) |
| src/tests/serde.rs | 2 | discard | serde feature out of scope |
| src/tests/daylight_saving.rs | 2 | discard, re-express in-scope intent | in-crate; DST intent covered by generated zone tests (different zones/dates) |
| src/tests/datetime.rs | 2 | discard, re-express in-scope intent | in-crate |
| src/iter/* mods | ~25 | discard | in-crate unit tests of private iterator internals (counter_date, monthinfo) |
| src/parser/* mods | ~25 | discard | in-crate unit tests of private parser types (ContentLineCaptures, regex captures, error constructors) |
| src/validator/* + src/core/* mods | ~20 | discard | in-crate unit tests asserting private validator functions and error struct fields |

functions_in_scope: 317 (all in-crate)
functions_kept: 0 (generated-only)
functions_excluded: 317

## Dummy-passable patterns avoided in generation

- Every validation-error test pairs the `is_err()`/variant assertion with a
  positive sibling on the same surface (the corrected rule validating and
  producing a checked occurrence stream), so an always-erroring stub cannot
  collect failure-path points disproportionately.
- Occurrence assertions compare full `DateTime` values (instant + zone name
  where the zone is contractual), never just lengths.
- No test asserts error message text, `Debug` output, or iteration-guard
  internals; `Display` assertions target only the canonical property text the
  spec defines.
- Round-trip tests assert both the intermediate canonical string and the
  final stream, so a stub echoing input strings fails the stream check and a
  stub with a correct iterator but no serializer fails the string check.
