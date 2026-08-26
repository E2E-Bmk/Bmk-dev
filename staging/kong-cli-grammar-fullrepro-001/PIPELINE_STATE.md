# Pipeline State — kong-cli-grammar-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读）。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 1
eval_iter:  0
language:   go
updated:    2026-08-25
```

todo:
- [x] Stage 3 complete: oracle built (116 atomic + 33 integration), lint PASS,
      reference 149/149, dummy worst case 0.7%

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | hard gates pass: 6332 LOC non-test single package, 271 black-box test funcs, 5 public projections over one grammar node tree, zero runtime deps; v1.16.1 (2026-08-09) post-cutoff; scope_plan N/A |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | filter_notes.md recorded; entering spec drafting with probe rounds |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probe rounds R1-R78 against pinned v1.16.1: flag syntaxes (no -n=5, bool no detached value), negatable, passthrough, -- terminator, flag scope (ancestor flags after node entry only), command selection + default:"1"/withargs, sep/mapsep defaults, counter, enum errors flag vs positional, xor/and messages, precedence CLI>resolver>env>default, JSON key variants, interpolation ${var=fallback} + undefined-var New error, hooks order + AfterRun, Run chain leaf-to-root + auto-bound *Context, binding errors, help layouts (default/compact/tree/groups/aliases/context-sensitive), exit codes (help/version 0, parse 80, Fatalf 1, ExitCoder honoured), model fields, staged Trace/Resolve/Apply/Validate |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: may/can-phrasing scrubbed, Non-Goals conformant, 8 CVIs, 8 behavior sections, API catalog Name/Kind/Role, pure-library CLI prose |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | entering upstream test audit |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | all 290 upstream funcs audited: 271 black-box bound to alecthomas/assert/v2 (+repr goldens), 18 white-box in-package, several suites out of spec scope (Signature, tag internals, wrap goldens, platform mappers); 100% discard -> Track B early trigger; rewrite_audit.md on disk |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections (8 behavior sections, error-semantics table, 8 CVIs, 2 workflows) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | 149 tests written (116 atomic + 33 integration); ref-run corrections: hyphen-prefixed detached values rejected for all flags (spec_error, wording generalised beyond short flags), required flags render inline in usage line (spec_gap), Node.Depth counts below application root (spec_error), cmd cannot mix positionals with child commands (test grammar fix), suggestion appended for near-miss unknown flags (test fix), struct reuse across parses leaks xor state (tests use fresh grammars) |
| 9 | 2026-08-25 | S3B_REFERENCE | S3B_DUMMY | reference 149/149 vs pinned v1.16.1 checkout (0678fd30), also verified against published proxy module |
| 10 | 2026-08-25 | S3B_DUMMY | S3B_DUMMY | filter_iter=1: accept-all stub passed 2/149 — TestCustomNegationName (zero value coincided with negated expectation) and TestValueSetReflectsSource (empty Flags() skipped loop); both strengthened with non-vacuity guards; reference re-verified 149/149 |
| 11 | 2026-08-25 | S3B_DUMMY | S3_DONE | per-test dummy runs: accept-all 0/149 (0.0%), reject-all 1/149 (0.7%, TestMustPanicsOnGrammarError — failure_path inherently satisfied by rejecting stub) — PASS; lint symbol check verified live (injected CompletionOptions → LINT_FAIL at grammar_test.go::282), fresh LINT_PASS on disk post-edit; task.json/kept_nodeids/taxonomy/spec_test_map/dummy_result recorded; atomic positive share 78% |

---

## Go Catalogue Overrides（language=go，本批次适用）

- 构建 oracle 位于 `oracle/{atomic,integration}/*_test.go` + `oracle/go.mod`
  （module `{task}-oracle`，require target；评分时由 runner 注入 `replace`）。
- 测试 ID 形如 `atomic::TestName` / `integration::TestName`。
- dummy gate：同一 module path 的对抗性 stub 模块，`go mod edit -replace` 后
  运行完整 oracle，要求 <=10% 通过。
- reference gate：pinned upstream checkout `replace` 后运行完整 oracle，
  要求 100% 通过，结果落盘 `filter/reference_score.json`。
- lint：Go-enabled `oracle_import_lint.py` + 本任务 TARGET_IMPORTS 条目，
  输出落盘 `filter/lint_result.txt`，首行必须 `LINT_PASS`，时间戳晚于 oracle。
