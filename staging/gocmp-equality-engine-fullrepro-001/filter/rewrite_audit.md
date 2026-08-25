# Track A rewrite audit — gocmp-equality-engine-fullrepro-001

Upstream test tree at 9b12f36 (v0.7.0), cmp package only (cmpopts out of scope).

| upstream file | funcs | import type | rewrite attempt | result |
|---------------|-------|-------------|-----------------|--------|
| compare_test.go | 1 (TestDiff, ~1000 table cases) | black-box shell but imports cmpopts (out of scope), cmp/internal/flags (forces deterministic diff mode), cmp/internal/testprotos, cmp/internal/teststructs{,/foo1,/foo2}; every case's expected value is a byte-exact diff transcript from testdata/diffs golden files | assertions compare exact diff layout, which the spec (and upstream docs) declare unstable by design; the case table cannot be rewritten without replacing every golden transcript with behavioral assertions, which changes what each case verifies | discard; behavior families (kind rules, option semantics, cycles, path steps, reporter protocol) recovered in Track B |
| options_test.go | 1 (TestOptionPanic) | white-box (package cmp), constructs internal option structs directly | not rewritable: asserts on internal option construction paths, not public behavior | discard; public panic contracts recovered as generated failure-path tests |
| example_test.go, example_reporter_test.go | 0 tests (Examples) | black-box stdout examples | assert stdout text incl. unstable diff layout; intents folded into generated workflow tests | discard, intent recovered |

Summary: 0 of 2 upstream test functions liftable -> Track B early trigger
(100% of files discarded after rewrite assessment, > 50% threshold).

functions_in_scope: 2 (upstream Test funcs; both excluded above)
functions_kept: 0 (Track A)
functions_excluded: 2
Track B output: see spec_test_map.md.

Coverage-guided generation notes (S3B): generation targets were enumerated from
the spec section list (Equality Judgement, Options and Filters, Difference
Reporting, Traversal Reporting; every Error Semantics row; all 7 CVIs; both
Representative Workflows) plus the upstream suite's behavior families (kind
rules across all Go kinds, Equal-method dispatch incl. nil receivers, option
filtering and ambiguity, transformer recursion guard, unexported-field
permission, cycle detection, path-step accessors, reporter protocol). Expected
values were observed by executing the pinned reference v0.7.0 (probe programs
under wip/gocmp-equality-engine-fullrepro-001/probe); no reference source files
were used as assertion material. Diff assertions use only the spec'd emptiness
and -/+ prefix contracts, never layout.
