# Pipeline State — petgraph-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读参考）。
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
updated:    2026-08-25
```

todo:
- [ ] inventory upstream test functions (tests/*.rs external + in-crate mods) within scope
- [ ] per-file import/scope audit: which files import only in-scope public API
- [ ] write filter/rewrite_audit.md with per-file disposition before any oracle work

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (27183 src LOC with scope_plan; six projections of one adjacency store; petgraph-specific index contracts; builds on 1.83 with indexmap =2.7.1 pin) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec drafting from docs.rs 0.8.3 within scope_plan |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec.md v1: 6-layer, 5 behavior sections (construction/mutation, indices+adjacency, stable+keyed, visitors+adapters, analysis, pathfinding+MST), state model, error table, 8 CVIs, import surface + API catalog; all contracts verified by probe against pinned 0.8.3 |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
