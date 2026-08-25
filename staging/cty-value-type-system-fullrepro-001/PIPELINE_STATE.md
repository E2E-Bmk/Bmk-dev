# Pipeline State — cty-value-type-system-fullrepro-001

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
- [ ] 审计 83 个上游测试函数的导入面与放置（in-package vs external）
- [ ] 判定 Track A 可保留比例；<阈值则触发 Track B
- [ ] rewrite_audit.md 落盘

functions_in_scope: 83 (upstream Test funcs in cty+convert+json+msgpack)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | hard gates pass: in-scope 11776 LOC, 5 projections over one value/type fact source, deterministic table-driven suite; scope_plan excludes function/stdlib+gocty; v1.19.0 (2026-07-06) post-cutoff |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | filter_notes.md recorded; entering spec drafting with probe rounds |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | 5 probe rounds against pinned v1.19.0: equality ladder incl. refined-notnull unknown bools, number precision (0.1+0.2==0.3 parsed), div/mod-by-zero, set HasIndex panic (docs mismatch), marks propagation/flattening, refinement builder panics + known-answer ops, convert matrix incl. list->tuple unavailable, json/msgpack round trips + error texts |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: modal phrasing scrubbed (can/could), Non-Goals phrasing conformant, API catalogs as Name/Kind/Role, 7 CVIs, 9 behavior sections; capsule/function/gocty/gob in Non-Goals |
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
