# Track A rewrite audit — cty-value-type-system-fullrepro-001

Scope: upstream test files in `cty/`, `cty/convert/`, `cty/json/`, `cty/msgpack/`
at pinned v1.19.0 (83 `Test*` functions across 30 files).

## File-level audit

| file group | files | funcs | package decl | decision | reason |
|---|---|---|---|---|---|
| cty/*_test.go (white-box) | 15 | ~50 | `package cty` | DISCARD | in-package placement: tests compile inside the target package and reference unexported identifiers (`unknown`, set internals, refinement internals observed in walk_test/set_internals_test/type_test/value_ops_test/unknown_refinement_test); cannot exist in an external oracle module |
| cty/path_test.go, cty/marks_wrangle_test.go | 2 | 3 | `package cty_test` | DISCARD | marks_wrangle imports `cty/ctymarks` (out of spec scope); path_test's 2 funcs are golden-table mega-runners asserting `GoString` renderings of paths — repr-shaped, fails Q1; and 2 < 30 makes Track A non-viable regardless |
| convert/*_test.go | 6 | ~15 | `package convert` | DISCARD | in-package placement; mega-runners (public_test.go alone: 156 anonymous cases inside a handful of funcs) — one behavioural defect flips whole families at base-function granularity |
| json/*_test.go | 5 | ~10 | `package json` | DISCARD | in-package placement |
| msgpack/*_test.go | 2 | ~8 | `package msgpack` | DISCARD | in-package placement; also asserts internal msgpack byte layouts in places (implementation-shape) |

functions_in_scope: 83
functions_kept (Track A): 0
functions_excluded: 83 (100%)

## Track B trigger

Early trigger fires: all upstream files discarded at Step 1 (>50% threshold
exceeded; actual 100%). The dominant carrier problem is structural — upstream
tests are compiled into the target packages themselves (Go white-box test
placement), which no external oracle module can reproduce, and the surviving
external files are either out of scope or golden-repr runners.

Track B generation targets are enumerated from the spec: 9 behavior sections
(Type System; Value Construction and Content Model; Value Operations; Paths;
Marks; Unknown Values and Refinements; Conversion Engine; JSON Codec;
MessagePack Codec), the Error Semantics table, 7 Cross-View Invariants, and
2 Representative Workflows. Assertions are constructed from observed reference
behaviour at v1.19.0 (5 probe rounds recorded in PIPELINE_STATE history), not
from upstream test expectations.
