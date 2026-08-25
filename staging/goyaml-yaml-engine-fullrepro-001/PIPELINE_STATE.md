# Pipeline State — goyaml-yaml-engine-fullrepro-001

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
- [ ] audit all 140 upstream test funcs: imports, granularity, golden coupling
- [ ] Track A/B decision per suite area; rewrite_audit.md on disk

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | hard gates pass: 15260 LOC non-test, 140 black-box test funcs, 8 public projections over one document model, zero runtime deps; v1.19.2 (2026-01-08) post-cutoff; scope_plan recorded (expected_oracle_max=140) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | filter_notes.md recorded; entering spec drafting with probe rounds |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | probe rounds R1-R69 against pinned v1.19.2: scalar typing (uint64 non-negatives, 1e3-as-string, +.inf-as-string, yes/on-as-string), dup-key default rejection, field matching (lowercased, json-tag fallback, silent ignore), quoting families incl. Title/CAPS bool-likes and mixed-case exception, literal blocks, anchors (shared values, tag anchor/alias), merge keys, CommentMap round trip, Path read/filter/replace/merge/annotate, lexer Origin loss-freeness, parser docs/comments, NodeToValue/ValueToNode, converters, MapSlice, RawMessage, error types via errors.As, options battery |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: may-phrasing scrubbed, Format Conversion given bold subsections, quoting rules tightened to probed families; Non-Goals conformant; 8 CVIs; 8 behavior sections |
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
