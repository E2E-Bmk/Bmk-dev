# Pipeline State — casbin-policy-enforcement-fullrepro-001

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
- [x] Track B 生成测试：84（55 atomic + 29 integration），spec_test_map 全量落盘
- [x] reference gate: pinned v3.11.0 replace 后 84/84 = 100% pass（filter/reference_score.json）
- [x] dummy gate: 对抗性 stub 双变体，worst-case 5/84 = 6.0%（filter/dummy_result.txt）
- [x] lint LINT_PASS 落盘（filter/lint_result.txt，晚于全部 oracle 测试文件）
- [x] task.json + kept_nodeids + taxonomy 落盘

functions_in_scope: 233 (upstream Test funcs; all excluded, see rewrite_audit.md)
functions_kept: 0 (Track A)
functions_excluded: 233
generated_functions: 84 (Track B; 55 atomic + 29 integration)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | go-chi/chi rejected (router pkg 1785 LOC < 3000 hard gate); casbin kept; upstream tests in-package + fixture-bound -> Track B expected |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | 6-layer spec drafted from casbin.org docs + 4 probe rounds against pinned v3.11.0 |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probes verified all error fragments, effect folds, matcher functions, RBAC/domain queries, adapter round-trips; adapterless SavePolicy panics upstream -> kept out of scope |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass; RemovePolicies excluded from scope (non-atomic remove semantics not spec-worthy); no leakage words |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tree audited: in-package (package casbin) tests + examples/ fixture files + unexported assert helpers |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | 100% discard share -> Track B early trigger (rewrite_audit.md on disk) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections (6 behavior sections, error table, 7 CVIs, 2 workflows) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_DUMMY | 84 tests generated (55 atomic + 29 integration); dummy stub worst-case 5/84 = 6.0% <= 10% |
| 9 | 2026-08-25 | S3B_DUMMY | S3B_REFERENCE | filter_iter=1: TestLoadPolicyRebuildsRoleGraph reworked to file adapter (string-adapter RemovePolicy clears Line -> upstream quirk, not spec behavior); TestPriorityWithRoleRules assertion corrected after probe |
| 10 | 2026-08-25 | S3B_REFERENCE | S3B_DONE | reference 84/84 = 100% (filter/reference_score.json) |
| 11 | 2026-08-25 | S3B_DONE | S3_ORACLE_MERGE | single-track (B only), merge trivial; spec_test_map covers all 84 with section minimums met |
| 12 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | full oracle re-run against pinned v3.11.0: 84/84 |
| 13 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | lint LINT_PASS on disk; task.json/kept_nodeids/taxonomy landed; packet complete |

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
