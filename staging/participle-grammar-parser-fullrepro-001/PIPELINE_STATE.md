# Pipeline State — participle-grammar-parser-fullrepro-001

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
filter_iter: 0
eval_iter:  0
language:   go
updated:    2026-08-25
```

todo:
- [x] Track B 生成测试：104（72 atomic + 32 integration），spec_test_map 全量落盘
- [x] reference gate: pinned v2.1.4 replace 后 104/104 pass（filter/reference_score.json）
- [x] dummy gate: 对抗性 stub 双变体，worst-case 5/104 = 4.8% <= 10%（filter/dummy_result.txt）
- [x] lint LINT_PASS 落盘（含 alias 修正后 symbol 级检查注入验证：注入 UndeclaredBogusSymbol → LINT_FAIL，移除后 LINT_PASS）
- [x] task.json + kept_nodeids + taxonomy 落盘

functions_in_scope: 142 (upstream Test funcs; all excluded, see rewrite_audit.md)
functions_kept: 0 (Track A)
functions_excluded: 142
generated_tests: 104 (72 atomic + 32 integration)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | etree (2097 LOC), ini (2361), goquery (1588), mapstructure (2018), rrule-go (1473), viper (2280), buntdb (1691) all rejected on LOC hard gate; participle core 3403 LOC at v2.1.4 passes all hard gates; casbin withdrawn earlier as cross-branch duplicate |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | 6-layer spec drafted from README/TUTORIAL/godoc + 4 probe rounds against pinned v2.1.4 |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probes verified: EBNF casing/format, bool-capture-true, string concat capture, per-token TextUnmarshaler, iteration guard, first-match-wins lexer order, error taxonomy fields, Wrapf position keep, elided explicit match |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass after fixes: modal verbs removed, API catalog converted to Name/Kind/Role tables, Appendix A/B aligned to batch style; ebnf subpackage + codegen + backrefs in Non-Goals |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | entering upstream test audit |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | 142 upstream tests all depend on third-party assert/repr modules + repr goldens; 100% discard -> Track B early trigger |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections (6 behavior sections, error table, 7 CVIs, 2 workflows) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | 104 tests written (72 atomic + 32 integration); ref-run fixes: EBNF title-casing (spec updated per observed v2.1.4 behaviour), Unquote invalid-escape input, lookahead test redesigned around backtracking |
| 9 | 2026-08-25 | S3B_REFERENCE | S3B_DUMMY | reference 104/104 vs pinned v2.1.4 |
| 10 | 2026-08-25 | S3B_DUMMY | S3_DONE | dummy stub accept-variant 5/104 (4.8%), reject-variant 4/104 (3.8%); explicit `participle` import alias added so lint symbol check covers /v2 module path (verified via injected violation → LINT_FAIL); final lint LINT_PASS on disk |

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
