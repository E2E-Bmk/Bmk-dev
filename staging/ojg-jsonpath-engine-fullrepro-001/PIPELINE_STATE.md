# Pipeline State — ojg-jsonpath-engine-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读参考，不在此复制）。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  1
filter_iter: 0
eval_iter:  0
functions_in_scope: 0
updated:    2026-08-26
```

todo:
- [x] Stage 3 complete: oracle 153 tests (131 atomic + 22 integration),
      reference 153/153, dummy worst 0.0%, LINT_PASS on disk

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | all hard gates pass: jp package 10916 src LOC >= 3000 (no generated code, zero external deps); path-expression fact source with >= 5 public projections (normalized string form, Get/First/Has/Locate selection, Set/Del/Remove/Modify mutation, Walk enumeration, PathMatch + filter Equation views); 159 upstream test funcs in 19 files, 18/19 external black-box (jp_test) but all carry module-level out-of-scope ojg imports (tt/oj/sen/alt/pretty/gen) -> Track B expected; JSONPath saturation risk mitigated by binding to pinned v1.28.5 observables (dialect diverges from RFC 9535; tag is 4 days old, post-cutoff); scope_plan target_subdomain=jp-over-native-go-data, expected_oracle_max=170 |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 from go doc -all + README + 51 probe rounds vs pinned v1.28.5: 8 behavior sections, 8 CVIs, 25-row Error Semantics (exact texts incl. position-and-source parse errors and per-operation ending-fragment rules); dialect edges bound to pinned observables (wildcard spelling retention, descent rendering collapse and its reparse failure, existence-not-truthiness bare-path filters, null vs Nothing vs missing, case-insensitive struct field match, Del nil-holes vs Remove excision, Set auto-creation rules, map-order nondeterminism stated as unspecified); all 25 validation checks + style gate pass (escape-hatch word fixed, leakage greps clean) |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body ships without internal header (Definition A); gen/streaming/procedures/custom-collections/struct-mutation declared out of scope in Non-Goals |
| 5 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | 19 upstream test files classified: 18 external jp_test but every substantive file imports out-of-scope sibling packages (tt asserts universal; oj/sen/pretty serialization goldens; gen typed-node variants; alt fixtures); norm_test.go in-package white-box no-assert smoke; per-file classification in filter/rewrite_audit.md |
| 6 | 2026-08-26 | S3A_REWRITE | S3B_TRIGGER | rewrite attempts fail for all 19 files (assert layer + serialization-golden expectations are bidirectional carriers; golden-to-value conversion changes what tests verify); functions_in_scope=0, discard rate 100% > 50% -> Track B early trigger; rewrite_audit.md on disk (hard-gate file) |
| 7 | 2026-08-26 | S3B_TRIGGER | S3B_GENERATE | Go task: Python coverage tooling n/a; generation targets enumerated per spec section with per-section minimums (8 behavior sections x >=4, Error Semantics >=4, 8 CVIs x >=2 integration, workflows >=4); reference observed execute-only via 51 probe rounds recorded in filter_notes.md |
| 8 | 2026-08-26 | S3B_GENERATE | S3B_LINT | 131 atomic tests hand-written across 10 suites (parse/build/strings/select/reflect/filter/equation/mutate/walkloc/errors) + 22 integration tests keyed to the 8 CVIs (2-3 each) + 6 workflows; generation probes produced three spec corrections (spec_iter 1), all narrowing to observed behaviour, none widening the surface: descent-last Set creates the named key in every visited map; CVI 6 scoped to targets without negative index fragments (spec's own PathMatch rule makes them unmatchable); equation-rendering parenthesization guarantee scoped to binary-operator nesting (reference folds trailing operators into a negated group); constructor-built root-anchored Get operands excluded from spec and oracle (parsed equations resolve $-refs, built ones do not); all tests pass vs pinned v1.28.5 |
| 9 | 2026-08-26 | S3B_LINT | S3B_REFERENCE | spec_test_map.md complete (153 rows, node ids diffed clean against go test -list output); kept_nodeids + taxonomy.jsonl derived; task registered in Go lint TARGET_IMPORTS; Go lint extension fixed for single-letter builder names (A..X): backtick-declared code tokens accepted, fence-aware span parsing, undeclared single letters still fail (verified live: injected jp.Q + jp.CompileScript -> LINT_FAIL, removed -> LINT_PASS); all 9 prior Go/Python tasks re-linted clean after the tool change |
| 10 | 2026-08-26 | S3B_REFERENCE | S3B_DUMMY | reference 153/153 (131 atomic + 22 integration) against published module v1.28.5 and re-verified via go mod replace to the pinned source clone; reference_score.json recorded |
| 11 | 2026-08-26 | S3B_DUMMY | S3_DONE | per-test dummy runs (adversarial stub at github.com/ohler55/ojg/jp, accept-all echo-and-empty + reject-all errors; stub compiles clean, go vet exit 0): first accept run exposed 1 vacuous pass (TestBuiltEqualsParsed echo round trip) -> anchored with built-form text + expected values; TestNewSliceUnset empty-iteration vacuity fixed pre-run (asserts 3 parts); final accept 0/153 (0.0%), reject 0/153 (0.0%); reference re-verified 153/153 after strengthening; fresh LINT_PASS post-edit (lint newer than every oracle test file); task.json/dummy_result recorded |
