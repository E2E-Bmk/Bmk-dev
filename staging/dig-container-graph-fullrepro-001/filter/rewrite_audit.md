# Track A rewrite audit — dig-container-graph-fullrepro-001

Upstream test tree at af45368 (v1.19.0), root package only.

| upstream file | funcs | import type | rewrite attempt | result |
|---------------|-------|-------------|-----------------|--------|
| dig_test.go | 35 (+~165 t.Run subtests) | black-box but wraps every operation in internal/digtest (require-asserting container wrapper) and internal/digclock | wrapper is removable mechanically, but the subtest bodies mix in-scope behavior with out-of-scope surface (WithProviderCallback, DryRun, LocationForPC, FillProvideInfo) inside shared table drivers; disentangling changes what each subtest verifies | discard; in-scope intents (provide/invoke semantics, tags, groups, cycles) recovered in Track B |
| scope_test.go | 4 | internal/digtest wrapper | same wrapper saturation; scope visibility intents recovered as generated black-box tests | discard, intent recovered |
| decorate_test.go | 4 | internal/digtest wrapper | decoration intents (scope isolation, groups, already-decorated) recovered in Track B | discard, intent recovered |
| stringer_test.go | 1 | internal/digtest + exact multi-line String() snapshot | exact-output snapshot; structural intent (nodes:/values: blocks) recovered as containment assertions | discard, intent recovered |
| visualize_test.go | 3 | internal/digtest + internal/dot + testdata golden .dot files | golden-file comparisons; structural intent (digraph output mentions produced types) recovered | discard, intent recovered |
| container_test.go, provide_test.go, param_test.go, result_test.go, group_test.go, error_test.go, constructor_test.go, scope_int_test.go, dig_int_test.go, visualize_int_test.go, visualize_golden_test.go | 21 | white-box (package dig), assert unexported node/param/result shapes, digreflect/dot internals | not rewritable: assertions target internal object graphs, not public behavior | discard |
| example_test.go | 0 tests (11 Examples) | black-box stdout examples | assert stdout text; intents folded into workflow tests | discard, intent recovered |

Summary: 0 of 72 upstream test functions liftable -> Track B early trigger
(100% of files discarded after rewrite assessment, > 50% threshold).

functions_in_scope: 72 (upstream Test funcs; all excluded above)
functions_kept: 0 (Track A)
functions_excluded: 72
Track B output: see spec_test_map.md.

Coverage-guided generation notes (S3B): generation targets were enumerated
from the spec section list (6 behavior sections, every Error Semantics row,
all 7 CVIs, both Representative Workflows) plus the upstream suite's behavior
families (scope trees, value groups incl. flatten/soft, deferred cycle
verification, decorator layering, error-chain classification, String/DOT
projections). Expected values were observed by executing the pinned reference
v1.19.0 (probe logs summarized in filter_notes.md source_boundary); no
reference source files were used as assertion material.
