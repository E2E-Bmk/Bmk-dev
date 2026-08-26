# Pipeline State — gocmp-equality-engine-fullrepro-001

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
- [x] spec.md 六层结构完成，行为经 pinned reference 探针核实（consolidated probe 全项通过）
- [x] Track A 重写审计（rewrite_audit.md）：0/2 upstream 函数可迁移 → Track B
- [x] Track B 生成 87 tests（54 atomic + 33 integration），spec_test_map.md 全行覆盖
- [x] reference gate: 87/87 pass（filter/reference_score.json）
- [x] dummy gate: 对抗性 stub 双变体，worst-case 3/87 = 3.4% <= 10%（filter/dummy_result.txt）
- [x] lint: LINT_PASS（filter/lint_result.txt，Go-enabled lint，时间戳晚于 oracle；注入违规自检通过）
- [x] task.json language=go, taxonomy + stats 落盘

functions_in_scope: 2 (upstream Test funcs; all excluded, see rewrite_audit.md)
functions_kept: 0 (Track A)
functions_excluded: 2
oracle_count: 87

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | golang-jwt/jwt rejected (LOC + closed standard); go-cmp kept; upstream tests are golden-transcript mega-runners -> Track B expected |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | 6-layer spec drafted from godoc + behavior probes against pinned v0.7.0 |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | consolidated probe: all panic fragments, nil-method dispatch, cycle semantics, reporter balance, path renderings, filter scoping, embedding steps verified against reference |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass; diff-layout claims limited to emptiness + prefix contract; no leakage words |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream tree audited: 1 golden-transcript mega-runner (TestDiff, ~1000 cases) + 1 white-box (package cmp) + Examples |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | 100% discard share -> Track B early trigger (rewrite_audit.md on disk) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections (4 behavior sections, error table, 7 CVIs, 2 workflows) + rule-ladder/kind/cycle/path families |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | first run: 3 failures (one-sided slice filter also neutralizes aligned modifications via remove+insert edit script; interface with differing concrete types judged without TypeAssertion descent); tests narrowed to spec'd behavior, spec unchanged (filter_iter=1) |
| 9 | 2026-08-25 | S3B_REFERENCE | S3B_DUMMY | adversarial stub (consistent projections both variants): accept-all 0/87, reject-all 3/87 = 3.4% |
| 10 | 2026-08-25 | S3B_DUMMY | S3_REFERENCE_RUN | final oracle vs reference: 87/87; per-section minimums verified (RW 4, State Model 3, CVI 14, Error 8) |
| 11 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | lint LINT_PASS on disk (violation-injection self-check); task.json + maps written; packet complete |

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
