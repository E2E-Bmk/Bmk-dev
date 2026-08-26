# Pipeline State — mvdansh-shell-syntax-fullrepro-001

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
filter_iter: 1
eval_iter:  0
functions_in_scope: 0
updated:    2026-08-26
```

todo:
- [x] Stage 3 complete: oracle built (144 atomic + 26 integration), lint PASS,
      reference 170/170, dummy accept 0.6% / reject 1.8%
- [ ] awaiting Stage 4+ (out of scope for this packet)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | all hard gates pass: in-scope LOC 9123 >= 3000; AST fact source with 7 public projections; upstream tests present (white-box mega-tables -> Track B expected); shell-standard saturation risk noted and mitigated by binding to v3.13.1 observables; scope_plan target_subdomain=syntax+typedjson, expected_oracle_max=170 |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec v1 written from full API dump (216 exported decls) + 60 probe rounds against v3.13.1 (positions, error catalog, printer rules incl. minify case compression, quote failures, typedjson shape, variant gating, recovery, brace/simplify rewrites) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | all 25 validation checks pass: phrasing fixes applied (no can/may outside quoted error texts, exact SpaceRedirects/Minify scope, backquoted error texts, table pipe escapes); 8 CVIs spanning parse/print/json/walk/quote/error domains; 7 behavior sections with narrative flow |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body ships without internal header (Definition A); zsh grammar + KeepPadding + DebugPrint declared out of scope in Non-Goals/import surface |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | 12 upstream test files classified: 10 in-package white-box (unexported AST-literal helpers + fileTests mega-table + shell-out confirmation), example_test.go golden-stdout examples, typedjson_test golden-file walker with qt dep |
| 7 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite attempts fail for all files (carrier is the in-package declaration itself; mega-tables not extractable per-function); discard rate 100% > 50%; rewrite_audit.md landed; functions_in_scope=0 |
| 8 | 2026-08-25 | S3B_TRIGGER | S3B_COVERAGE | rewrite_audit.md verified present with per-file failure_reason |
| 9 | 2026-08-25 | S3B_COVERAGE | S3B_GENERATE | Go task: Python coverage tooling n/a; generation targets enumerated per spec section with per-section minimums (7 behavior sections x >=4, Error Semantics >=4, 8 CVIs x >=2 integration, workflows >=4); probes R61-R69 resolved open questions (test-expr right associativity — spec corrected; byte-column counting; BraceExp not printable; walk pruning; minify reparse equality) |
| 10 | 2026-08-25 | S3B_GENERATE | S3B_LINT | 144 atomic tests hand-written across 8 suites, all pass vs pinned v3.13.1 first run; integration generation probes disproved three drafted spec claims — CVI 1 narrowed to layout options (SingleLine output can fail to reparse: `& done wait`), CVI 8 restated as minify-reparse+minify-fixpoint (line joins change default layout), CVI 3/decoding restated to the actual decode registry (Stmt/Redirect/Assign/Comment encode but do not decode), heredoc End qualified (later same-line redirect ends the statement before the body) — spec corrected to observed behaviour (spec_iter 1), no surface widening; 26 integration tests keyed to the 8 CVIs |
| 11 | 2026-08-25 | S3B_LINT | S3B_REFERENCE | spec_test_map.md complete (170 rows, node ids diffed clean against oracle); kept_nodeids + taxonomy.jsonl derived; task registered in Go lint TARGET_IMPORTS; LINT_PASS on disk; lint verified live (injected UndeclaredProbeSymbol → LINT_FAIL at pos_test.go, then removed) |
| 12 | 2026-08-26 | S3B_REFERENCE | S3B_DUMMY | reference 170/170 (144 atomic + 26 integration) via replace against pinned checkout 2f3f5e3, and re-verified against published proxy module v3.13.1; reference_score.json recorded |
| 13 | 2026-08-26 | S3B_DUMMY | S3_DONE | per-test dummy runs (adversarial stub at mvdan.cc/sh/v3): first accept-mode run exposed 8 vacuous integration passes → spec-grounded non-vacuity guards added (mustParse stmt floor, non-empty newline-terminated prints, walk node floor, Type-tag presence, genuinely-simplifiable sources, File.Name and key-presence positives) → final accept 1/170 (0.6%: TestZeroLinePosInvalid, zero-value contract, inherent), reject 3/170 (1.8%: + two variant-gating failure_path tests whose exact error texts are not spec-declared, so error-only assertion kept per no-widening rule); reference re-verified 170/170 after every change; fresh LINT_PASS post-edit; task.json/dummy_result recorded |
