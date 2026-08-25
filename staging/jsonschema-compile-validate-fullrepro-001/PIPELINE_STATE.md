# Pipeline State — jsonschema-compile-validate-fullrepro-001

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
spec_iter:  1
filter_iter: 1
eval_iter:  0
language:   go
updated:    2026-08-25
```

todo:
- [x] spec.md 六层结构完成，行为经 pinned reference 探针核实
- [x] Track A 重写审计（rewrite_audit.md）：0/27 upstream 函数可迁移 → Track B
- [x] Track B 生成 79 tests（52 atomic + 27 integration），spec_test_map.md 全行覆盖
- [x] reference gate: 79/79 pass（filter/reference_score.json）
- [x] dummy gate: 对抗性 stub，2/79 = 2.5% <= 10%（filter/dummy_result.txt）
- [x] lint: LINT_PASS（filter/lint_result.txt，Go-enabled lint，时间戳晚于 oracle）
- [x] task.json language=go, taxonomy + stats 落盘

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep; Go test import pre-screen: upstream tests are data-driven suite runners + examples, Track B planned |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | 6-layer spec drafted from behavior probes against pinned v6.0.3 checkout |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: SchemeURLLoader/LoadURLError wrapping inaccuracy found via probe, spec corrected (spec_iter=1) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | all sections verified against reference behavior; no benchmark language; no internal symbols |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream test tree audited: suite runners (4700 external JSON cases), white-box in-package tests, golden files |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | 100% discard share → Track B early trigger (rewrite_audit.md) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections + upstream behavior families; 79 tests generated |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | first run: 1 failure (TestEmbeddedResourceWithIDIsReferenceable over-asserted standalone compile); test narrowed to spec'd behavior, not spec widened |
| 9 | 2026-08-25 | S3B_REFERENCE | S3B_DUMMY | adversarial stub: 6 weak tests found; absence-only test merged away, consistency tests gained ground-truth contrasts (filter_iter=1) |
| 10 | 2026-08-25 | S3B_DUMMY | S3_REFERENCE_RUN | final oracle re-run vs reference: 79/79; dummy 2/79=2.5% |
| 11 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | lint LINT_PASS on disk; task.json written; packet complete |

---

## Go Catalogue Overrides（language=go，本批次适用）

- 构建 oracle 位于 `oracle/{atomic,integration}/*_test.go` + `oracle/go.mod`
  （module `{task}-oracle`，require target `v0.0.0`，评分时由 runner 注入
  `replace`）。
- 测试 ID 形如 `atomic::TestName` / `integration::TestName`
  （`harness/runners/go.py` 的 discover/taxonomy 约定）。
- dummy gate：同一 module path 的对抗性 stub 模块（零值返回 + 非 nil error，
  非 panic），`go mod edit -replace` 后运行完整 oracle，要求 0 通过。
- reference gate：pinned upstream checkout `replace` 后运行完整 oracle，
  要求 100% 通过，结果落盘 `filter/reference_score.json`。
- lint：Go-enabled `oracle_import_lint.py`（origin/go-tasks-20260821 版本 +
  本任务 TARGET_IMPORTS 条目），输出落盘 `filter/lint_result.txt`，首行必须
  `LINT_PASS`，且时间戳晚于所有 oracle 测试文件。
