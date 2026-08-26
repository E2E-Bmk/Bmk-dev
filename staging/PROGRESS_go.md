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
    `-- dummy_result.txt        adversarial dummy run evidence (worst case <= 10%)
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
"participle-grammar-parser-fullrepro-001": [
    "github.com/alecthomas/participle/v2",
    "github.com/alecthomas/participle/v2/lexer",
],
"cty-value-type-system-fullrepro-001": [
    "github.com/zclconf/go-cty/cty",
    "github.com/zclconf/go-cty/cty/convert",
    "github.com/zclconf/go-cty/cty/json",
    "github.com/zclconf/go-cty/cty/msgpack",
],
"goyaml-yaml-engine-fullrepro-001": [
    "github.com/goccy/go-yaml",
    "github.com/goccy/go-yaml/ast",
    "github.com/goccy/go-yaml/parser",
    "github.com/goccy/go-yaml/lexer",
    "github.com/goccy/go-yaml/token",
],
"kong-cli-grammar-fullrepro-001": [
    "github.com/alecthomas/kong",
],
"mvdansh-shell-syntax-fullrepro-001": [
    "mvdan.cc/sh/v3/syntax",
    "mvdan.cc/sh/v3/syntax/typedjson",
],
"xpath-query-engine-fullrepro-001": [
    "github.com/antchfx/xpath",
],
"ojg-jsonpath-engine-fullrepro-001": [
    "github.com/ohler55/ojg/jp",
],
```

Lint caveat for `/vN` module paths: `go_target_symbols` derives the package
alias from the import path's last segment, so `.../participle/v2` maps to `v2`
and unaliased imports silently skip the symbol check. Oracles for such modules
use an explicit import alias (`participle "github.com/alecthomas/participle/v2"`);
the participle packet's symbol check was verified live by injecting an
undeclared symbol (LINT_FAIL observed) before recording the final LINT_PASS.

Lint caveat for single-letter Go names (ojg's builder shorthands `A`..`X`):
`spec_words` extraction requires two or more characters, so a single-letter
exported name could never pass the symbol check even when the spec declares
it. The Go branch of the lint extension now accepts a single-letter symbol
exactly when the spec declares that letter as a code token (inside a fenced
block or a backticked span, with fences cut out before span parsing so ```
fences cannot shift backtick pairing). Undeclared single letters still fail
(verified live: injected `jp.Q` -> LINT_FAIL); all nine earlier task packets
re-linted LINT_PASS after the tool change.

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
| 4 | participle-grammar-parser-fullrepro-001 | alecthomas/participle @ v2.1.4 | S3_DONE | 104 (72+32) | 104/104 | Track B (upstream tests bound to alecthomas/assert+repr goldens); dummy worst-case 5/104=4.8% |
| 5 | cty-value-type-system-fullrepro-001 | zclconf/go-cty @ v1.19.0 | S3_DONE | 132 (96+36) | 132/132 | Track B (upstream 81/83 in-package white-box); dummy worst-case 6/132=4.5% after strengthening pass (initial accept-stub 15.2% → negative controls + native-content assertions); module requires go >= 1.25 |
| 6 | goyaml-yaml-engine-fullrepro-001 | goccy/go-yaml @ v1.19.2 | S3_DONE | 134 (97+37) | 134/134 | Track B (upstream mega-tables import internal/errors; path/lexer suites golden-bound); dummy worst-case 1/134=0.7% after non-vacuity fix (initial 2/134, one vacuous all-nil round-trip passer); 3 spec_error fixes during ref run (validator FieldError-slice annotation, trailing-newline Origin loss, ReplaceWithReader comment drop) |
| 7 | kong-cli-grammar-fullrepro-001 | alecthomas/kong @ v1.16.1 | S3_DONE | 149 (116+33) | 149/149 | Track B (upstream bound to alecthomas/assert+repr; Signature/tag-internal/wrap-golden suites out of scope); dummy accept 0/149, reject 1/149=0.7% (Must-panics failure_path, inherent); spec corrections during ref run (hyphen-prefixed detached values, required flags in usage line, Depth semantics) |
| 8 | mvdansh-shell-syntax-fullrepro-001 | mvdan/sh @ v3.13.1 | S3_DONE | 170 (144+26) | 170/170 | Track B (upstream 10/12 files in-package white-box AST-literal mega-tables); dummy accept 1/170=0.6% (zero-Pos contract, inherent), reject 3/170=1.8% (+2 variant-gating failure_path, error texts not spec-declared); spec corrections from generation probes (CVI 1 scoped to layout options — SingleLine output can fail to reparse; CVI 8 → minify fixpoint; typedjson decode registry — Stmt/Redirect/Assign/Comment encode-only; heredoc statement-End vs later same-line redirect) |
| 9 | xpath-query-engine-fullrepro-001 | antchfx/xpath @ v1.3.8 | S3_DONE | 160 (132+28) | 160/160 | Track B (upstream 9/10 files in-package white-box: unexported query/iterator interfaces + shared TNode fixture-runner layer); dummy accept 0/160, reject 0/160 after strengthening 3 String()-echo/constant-integer tests with behavioural anchors; spec corrections from probes (NodeNavigator thirteen methods; non-standard `not()` — string/number arguments return false regardless of value); upstream panic zones excluded from scope (mixed boolean comparisons, substring NaN bounds, reverse-axis position()) |
| 10 | ojg-jsonpath-engine-fullrepro-001 | ohler55/ojg @ v1.28.5 | S3_DONE | 153 (131+22) | 153/153 | Track B (all 19 upstream files import out-of-scope siblings: tt asserts + oj/sen/pretty goldens + gen/alt variants); dummy accept 0/153, reject 0/153 after anchoring 1 echo round-trip vacuity (TestBuiltEqualsParsed) + NewSlice empty-iteration; spec corrections from generation probes (descent-last Set creates keys in every visited map; CVI 6 scoped to non-negative-index targets per own PathMatch rule; equation parenthesization guarantee scoped to binary nesting — reference folds operators into negated groups); built root-anchored Get operands excluded (parsed equations resolve $-refs, constructor-built do not); tag 4 days pre-packet |

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
| alecthomas/participle | SELECTED | 6759 LOC, 146 test funcs | parser-builder: struct-tag grammar mini-language, lexer defs, EBNF projection; Track B |
| goccy/go-yaml | SELECTED | 13130 LOC, 140 black-box test funcs | YAML engine: decode/encode, PathString queries, anchors, source-annotated errors, lexer/parser projections; Track B |
| alecthomas/kong | SELECTED | 6332 LOC @ v1.16.1, 290 test funcs | CLI grammar engine: struct-tag DSL, parse+help+model+resolution+execution projections; Track B |
| antchfx/xpath | SELECTED | 4729 LOC (4729 in scope), 83 test funcs | XPath 1.0 engine over caller-supplied NodeNavigator: compile/select/evaluate projections, namespace dual-mode matching; Track B |
| zclconf/go-cty | SELECTED | 13657 LOC, 165 test funcs | value/type system: conversions, unification, refinements/marks, json/msgpack round trips; Track B |
| mvdan/sh | SELECTED | 16185 LOC (9123 in scope), 105 test funcs | shell syntax engine: parse/print round trip, positions, quoting, typed JSON; Track B |
| ohler55/ojg | SELECTED | 10916 LOC in scope (jp pkg; module ~31k), 159 test funcs | JSONPath dialect engine: path parse/build/normalize + get/set/del/modify/walk/match projections over native Go data; scope_plan jp-only, max 170; Track B confirmed |

## Dedup register (Go repos already taken on `origin/go-tasks-20260821`)

spf13/afero, etcd-io/bbolt, casbin/casbin, expr-lang/expr, itchyny/gojq,
pressly/goose, nutsdb/nutsdb, dgraph-io/ristretto, d5/tengo,
go-playground/validator. Main `tasks/` contains no Go tasks. Any repo above is
off-limits for this batch.
