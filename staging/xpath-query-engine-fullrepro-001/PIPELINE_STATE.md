# Pipeline State — xpath-query-engine-fullrepro-001

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
- [x] Stage 3 complete: oracle built (132 atomic + 28 integration), lint PASS,
      reference 160/160, dummy accept 0.0% / reject 0.0%
- [ ] awaiting Stage 4+ (out of scope for this packet)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | all hard gates pass: 4729 src LOC >= 3000; compiled-expression fact source with Select/Evaluate/error/String projections; 83 upstream test funcs (9/10 files white-box -> Track B expected); closed-standard saturation risk noted with v1.3.8-observable mitigation (same pattern as mvdansh packet); scope_plan N/A |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 from go doc -all + README + 58 probe rounds vs pinned v1.3.8: 8 behavior sections, 8 CVIs, 26-row Error Semantics (exact compile-error texts incl. arity quirks: floor/round report ceiling, substring-after reports substring-before), namespace dual-mode matching (prefix-literal vs NamespaceURL), union concatenation order, coercion/formatting rules; upstream panics excluded from scope (boolean comparisons, substring NaN bounds, reverse-axis position()); all 25 validation checks + style gate pass (forbidden-phrasing and leakage greps clean) |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceeding to Stage 3 |
| 5 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | 9/10 upstream test files in-package white-box (unexported query/iterator/loadingCache + shared TNode fixture-runner layer); doc_test.go external but a single golden-stdout Example; per-file classification in filter/rewrite_audit.md |
| 6 | 2026-08-26 | S3A_REWRITE | S3B_TRIGGER | rewrite attempts fail for all 10 files (runner/fixture carrier is bidirectional); functions_in_scope=0, discard rate 100% > 50% -> Track B early trigger; rewrite_audit.md on disk (hard-gate file) |
| 7 | 2026-08-26 | S3B_TRIGGER | S3B_GENERATE | Go task: Python coverage tooling n/a; generation targets enumerated per spec section with per-section minimums (8 behavior sections x >=4, Error Semantics >=4, 8 CVIs x >=2 integration, workflows >=4); reference observed execute-only via 58 probe rounds recorded in filter_notes.md |
| 8 | 2026-08-26 | S3B_GENERATE | S3B_LINT | 132 atomic tests hand-written across 8 suites (compile/select/navigator/axes/namespace/predicates/operators/functions/errors) + 28 integration tests keyed to the 8 CVIs; generation probes fixed two drafted spec claims before landing — NodeNavigator method count corrected to thirteen, `not()` restated to the observed non-standard rule (string/number arguments return false regardless of value); spec corrected to observed behaviour (spec_iter 1), no surface widening; all tests pass vs pinned v1.3.8 |
| 9 | 2026-08-26 | S3B_LINT | S3B_REFERENCE | spec_test_map.md complete (160 rows, node ids diffed clean against oracle); kept_nodeids + taxonomy.jsonl derived; task registered in Go lint TARGET_IMPORTS; LINT_PASS on disk; lint verified live (injected undeclared symbol -> LINT_FAIL, then removed -> LINT_PASS) |
| 10 | 2026-08-26 | S3B_REFERENCE | S3B_DUMMY | reference 160/160 (132 atomic + 28 integration) against published module v1.3.8 and re-verified via go mod replace wiring; reference_score.json recorded |
| 11 | 2026-08-26 | S3B_DUMMY | S3_DONE | per-test dummy runs (adversarial stub at github.com/antchfx/xpath, accept-all empty results + reject-all compile errors): first accept-mode assessment exposed 3 would-be vacuous passes (String()-echo and NodeType constant-integer assertions) -> behavioural anchors added (selection assertions on real documents) -> final accept 0/160 (0.0%), reject 0/160 (0.0%); reference re-verified 160/160 after strengthening; fresh LINT_PASS post-edit (lint newer than every oracle test file); task.json/dummy_result recorded |
