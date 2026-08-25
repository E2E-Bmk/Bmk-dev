# Go Stage 1-3 batch progress

Branch: `cursor/8-26-50tasks-go-a9d6`. Deliverable: 10 Go task packets at Stage 3
completion (S3_DONE), each under `staging/{task_id}/`.

## Packet layout (Definition A)

```
staging/{task_id}/
|-- spec.md                     candidate-visible body only (internal header omitted;
|                               source_boundary recorded in filter_notes.md)
|-- task.json                   language=go, taxonomy, stats, repo_commit
|-- PIPELINE_STATE.md           state machine instance, S1_SCREENING -> S3_DONE
|-- filter_notes.md             Stage 1 evidence brief + source_boundary
|-- oracle/
|   |-- go.mod                  module {task}-oracle, requires target at v0.0.0
|   |-- go.sum                  dependency snapshot from the reference run
|   |-- atomic/*_test.go        package atomic
|   `-- integration/*_test.go   package integration
`-- filter/
    |-- spec_test_map.md        one row per test, spec_section per row, footer totals
    |-- kept_nodeids.txt        suite::TestName, covered rows only
    |-- taxonomy.jsonl          {"taxonomy_key": "atomic::TestX", "layer": "atomic"}
    |-- lint_result.txt         oracle_import_lint output, first line LINT_PASS
    |-- reference_score.json    reference run at pinned version, must be 100%
    `-- dummy_result.txt        adversarial dummy run evidence (0 passes required)
```

## Harness note (required to reproduce lint results)

`harness/oracle_import_lint.py` on `main` has no Go oracle layout support and no
`TARGET_IMPORTS` entries for these tasks; the write scope of this batch is
`staging/` only, so the harness was not modified on this branch. Lint results in
each packet were produced with the Go-enabled lint from branch
`origin/go-tasks-20260821` (commit 85c6278: adds `go_target_symbols` and the
`oracle/atomic` + `oracle/integration` layout detection), run from a gitignored
copy under `wip/_tools/harness/`, with the following entries appended to its
`TARGET_IMPORTS` copy (these must be added to `harness/target_imports.py` when
the packets graduate):

```python
"jsonschema-compile-validate-fullrepro-001": [
    "github.com/santhosh-tekuri/jsonschema/v6",
    "github.com/santhosh-tekuri/jsonschema/v6/kind",
],
"dig-container-graph-fullrepro-001": ["go.uber.org/dig"],
"gocmp-equality-engine-fullrepro-001": ["github.com/google/go-cmp/cmp"],
```

Reference runs execute `go test -json ./...` per suite against the pinned
upstream version wired in with `go mod edit -replace`, mirroring
`harness/runners/go.py` setup. Dummy runs use an adversarial stub module
(zero-value returns and non-nil errors, not panics) at the same module path.

## Status

| # | task_id | repo | state | oracle (atomic+integration) | reference | notes |
|---|---------|------|-------|-----------------------------|-----------|-------|
| 1 | jsonschema-compile-validate-fullrepro-001 | santhosh-tekuri/jsonschema @ v6.0.3 | S3_DONE | 79 (52+27) | 79/79 | Track B (upstream = data-driven suite runners); dummy 2/79=2.5% |
| 2 | dig-container-graph-fullrepro-001 | uber-go/dig @ v1.19.0 | S3_DONE | 99 (62+37) | 99/99 | Track B (upstream tests bound to internal/digtest); dummy worst-case 5/99=5.1% |
| 3 | gocmp-equality-engine-fullrepro-001 | google/go-cmp @ v0.7.0 | S3_DONE | 87 (54+33) | 87/87 | Track B (upstream = golden-transcript mega-runner + white-box); dummy worst-case 3/87=3.4% |

## Candidate selection log (CANDIDATES.md rows deferred; write scope is staging/ only)

| repo | status | metric | detail |
|------|--------|--------|--------|
| santhosh-tekuri/jsonschema | SELECTED | ~5.4k LOC core, 27 upstream test funcs + 4700 suite cases | JSON Schema 2020-12/draft-7 engine: lazy ref graphs, rational-number equality, output projections; Track B |
| uber-go/dig | SELECTED | ~6.0k LOC, 72 test funcs | reflection DI graph: scopes/groups/decorators, cycle detection, error tree + DOT projections; Track B |
| golang-jwt/jwt | REJECTED | 2371 LOC < 3000 hard gate | closed RFC 7519 standard, saturation risk; two derived views only |
| google/go-cmp | SELECTED | ~5.8k LOC (cmp + internals), 2 upstream test funcs (mega-runners) | equality rule ladder, option/filter mini-language, cycle tracking, 4 projections (Equal/Diff/Reporter/panics); Track B |
| go-chi/chi | REJECTED | router pkg 1785 LOC < 3000 | middleware/ is an unrelated utility collection; core alone under gate |
| casbin/casbin | RETIRED (duplicate) | full S3_DONE packet built (84 tests, ref 84/84, dummy 6.0%) then withdrawn | `origin/go-tasks-20260821` already ships QUALIFIED `tasks/casbin-policy-enforcement-fullrepro-001` (same repo, same instance_id); packet removed in this branch to honour the no-duplicates rule |
| beevik/etree | REJECTED | source 2097 LOC < 3000 (etree.go 1225 + helpers.go 409 + path.go 463) | XML tree + path queries; fails LOC hard gate |
| go-ini/ini | REJECTED | 2361 LOC < 3000 | INI engine; fails LOC hard gate |
| PuerkitoBio/goquery | REJECTED | 1588 LOC < 3000 | selector matching lives in cascadia dep; goquery alone is a thin traversal layer |
| go-viper/mapstructure | REJECTED | 2018 LOC < 3000 | decode-rules engine; fails LOC hard gate |
| teambition/rrule-go | REJECTED | 1473 LOC < 3000; RFC 5545 closed standard | dateutil.rrule is a high-saturation pattern |
| spf13/viper | REJECTED | 2280 LOC < 3000 | precedence logic thin; real work delegated to deps (mapstructure/cast/afero) |
| tidwall/buntdb | REJECTED | 1691 LOC < 3000; single-file library | also shape-overlaps nutsdb task on go branch |
| google/go-jsonnet | REJECTED | LOC dominated by generated stdast (~200k); heavy build | interpreter core viable but generated-code accounting and build weight make it a poor fit |
| alecthomas/participle | SELECTED | 6759 LOC, 146 test funcs | parser-builder: struct-tag grammar mini-language, lexer defs, EBNF projection; Track TBD |
| goccy/go-yaml | QUEUED (candidate) | 13130 LOC, 143 test funcs | YAML engine: decode/encode, PathString queries, anchors, source-annotated errors |
| alecthomas/kong | QUEUED (candidate) | 5629 LOC, 300 test funcs | CLI grammar engine: struct-tag DSL, parse+help+defaults+validation projections |
| antchfx/xpath | QUEUED (candidate) | 4032 LOC, 83 test funcs | XPath 1.0 engine over caller-supplied NodeNavigator |
| zclconf/go-cty | QUEUED (candidate) | 13657 LOC, 165 test funcs | value/type system: conversions, unification, functions, json/msgpack round trips |
| mvdan/sh | QUEUED (candidate) | 16185 LOC, 105 test funcs | shell syntax engine: parse/print round trip, positions, quoting rules |
| ohler55/ojg | QUEUED (candidate) | 30855 LOC, 835 test funcs | JSONPath (jp) + parser (oj) engines over native Go data |

## Dedup register (Go repos already taken on `origin/go-tasks-20260821`)

spf13/afero, etcd-io/bbolt, casbin/casbin, expr-lang/expr, itchyny/gojq,
pressly/goose, nutsdb/nutsdb, dgraph-io/ristretto, d5/tengo,
go-playground/validator. Main `tasks/` contains no Go tasks. Any repo above is
off-limits for this batch.
