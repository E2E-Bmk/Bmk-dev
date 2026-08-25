# Pipeline State — kong-cli-grammar-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读）。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S3A_IMPORT_AUDIT
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   go
updated:    2026-08-25
```

todo:
- [ ] audit all 290 upstream test funcs: imports, granularity, golden coupling
- [ ] Track A/B decision per suite area; rewrite_audit.md on disk

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | hard gates pass: 6332 LOC non-test single package, 271 black-box test funcs, 5 public projections over one grammar node tree, zero runtime deps; v1.16.1 (2026-08-09) post-cutoff; scope_plan N/A |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | filter_notes.md recorded; entering spec drafting with probe rounds |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probe rounds R1-R78 against pinned v1.16.1: flag syntaxes (no -n=5, bool no detached value), negatable, passthrough, -- terminator, flag scope (ancestor flags after node entry only), command selection + default:"1"/withargs, sep/mapsep defaults, counter, enum errors flag vs positional, xor/and messages, precedence CLI>resolver>env>default, JSON key variants, interpolation ${var=fallback} + undefined-var New error, hooks order + AfterRun, Run chain leaf-to-root + auto-bound *Context, binding errors, help layouts (default/compact/tree/groups/aliases/context-sensitive), exit codes (help/version 0, parse 80, Fatalf 1, ExitCoder honoured), model fields, staged Trace/Resolve/Apply/Validate |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: may/can-phrasing scrubbed, Non-Goals conformant, 8 CVIs, 8 behavior sections, API catalog Name/Kind/Role, pure-library CLI prose |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | entering upstream test audit |

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
