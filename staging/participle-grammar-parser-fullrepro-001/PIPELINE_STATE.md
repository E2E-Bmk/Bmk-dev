# Pipeline State — participle-grammar-parser-fullrepro-001

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
- [ ] audit upstream test tree: imports, golden reprs, in-repo helpers
- [ ] Track A/B decision -> rewrite_audit.md

functions_in_scope: 146 (upstream Test funcs at v2.1.4)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | etree (2097 LOC), ini (2361), goquery (1588), mapstructure (2018), rrule-go (1473), viper (2280), buntdb (1691) all rejected on LOC hard gate; participle core 3403 LOC at v2.1.4 passes all hard gates; casbin withdrawn earlier as cross-branch duplicate |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | 6-layer spec drafted from README/TUTORIAL/godoc + 4 probe rounds against pinned v2.1.4 |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probes verified: EBNF casing/format, bool-capture-true, string concat capture, per-token TextUnmarshaler, iteration guard, first-match-wins lexer order, error taxonomy fields, Wrapf position keep, elided explicit match |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass after fixes: modal verbs removed, API catalog converted to Name/Kind/Role tables, Appendix A/B aligned to batch style; ebnf subpackage + codegen + backrefs in Non-Goals |
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
