# Track A rewrite audit — jsonschema-compile-validate-fullrepro-001

Upstream test tree at b0fc661 (v6.0.3), root package only (cmd/jv is a
separate module, out of scope).

| upstream file | functions | import type | rewrite attempt | result |
|---------------|-----------|-------------|-----------------|--------|
| suite_test.go | TestSuites, TestExtra + helpers | data-driven runner over testdata/JSON-Schema-Test-Suite and testdata/Extra-Test-Suite | not rewritable: the behavioral content lives in ~4700 external JSON cases, not in the test functions; lifting the runner would ship the official conformance suite as the oracle (memorization-saturated, fixture-bound) | discard |
| validator_test.go | TestValidateInterface, TestNumberNormalization, ... | in-package white-box (package jsonschema) | uses unexported helpers and internal object shapes; behavioral intents (number normalization, interface acceptance) re-expressed as generated black-box tests | discard, intent recovered in Track B |
| compiler_test.go | TestCompileNonStd, ... | white-box | same as above; duplicate-resource and meta-validation intents recovered in Track B | discard, intent recovered |
| output_test.go | TestOutputFormats | golden-file comparison against testdata/marshal.json and debug.json | exact-output snapshot check; behavioral intent (output unit shapes) recovered as structural assertions in Track B | discard, intent recovered |
| loader_test.go, filepaths_test.go, util_test.go, draft_test.go, invalid_schemas_test.go, debug_test.go | misc | white-box + testdata-bound | not liftable | discard |
| example_*.go | 11 Example funcs | black-box (package jsonschema_test) | assert stdout text; example intents (compile/validate flow, custom loader) recovered as behavioral tests | discard, intent recovered |

Summary: 0 upstream functions liftable → Track B triggered (all files
discarded after rewrite assessment; discard share 100% > 50% early trigger).

functions_in_scope: 27 (upstream Test funcs; all excluded above)
functions_kept: 0 (Track A)
functions_excluded: 27
Track B output: 79 generated tests (52 atomic + 27 integration), see
spec_test_map.md.

Coverage-guided generation notes (S3B): instead of Python branch coverage,
generation targets were enumerated from the spec's section list (every H2/H3
behavior section, every Error Semantics row, every CVI) plus the upstream
suite's behavior families (reference graphs, dialect interop, output
formats, rational-number equality). Expected values were observed by
executing the pinned reference (see wip probe logs reproduced in
filter_notes.md difficulty shapes); no reference source files were used as
assertion material.
