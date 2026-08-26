# Pipeline State — xpath-query-engine-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读参考，不在此复制）。
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
functions_in_scope: 0
updated:    2026-08-26
```

todo:
- [ ] 审计上游测试文件 import 面（Track A 保留 vs Track B 重写判定）
- [ ] 记录审计结论到 filter_notes.md

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | all hard gates pass: 4729 src LOC >= 3000; compiled-expression fact source with Select/Evaluate/error/String projections; 83 upstream test funcs (9/10 files white-box -> Track B expected); closed-standard saturation risk noted with v1.3.8-observable mitigation (same pattern as mvdansh packet); scope_plan N/A |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 from go doc -all + README + 58 probe rounds vs pinned v1.3.8: 8 behavior sections, 8 CVIs, 26-row Error Semantics (exact compile-error texts incl. arity quirks: floor/round report ceiling, substring-after reports substring-before), namespace dual-mode matching (prefix-literal vs NamespaceURL), union concatenation order, coercion/formatting rules; upstream panics excluded from scope (boolean comparisons, substring NaN bounds, reverse-axis position()); all 25 validation checks + style gate pass (forbidden-phrasing and leakage greps clean) |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceeding to Stage 3 |
