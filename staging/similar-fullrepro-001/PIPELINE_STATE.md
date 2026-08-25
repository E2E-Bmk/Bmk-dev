# Pipeline State — similar-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读参考）。
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
updated:    2026-08-25
```

todo:
- [ ] (next stage) S4_SETUP: build task environment from repo_commit and run scorer end-to-end

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (diff engine, ~5009 LOC, 50 test fns, 7 public projections of one op stream; pinned 2.7.0 edition-2018 for rustc 1.83, 3.x needs 1.85) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | spec.md drafted from docs.rs 2.7.0 + README (6-layer structure): algorithms/hooks, op streams, grouping/similarity, text diffing, unified output, inline emphasis, utils/remap |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: modal phrasing fixed (2 `can` clauses), no leakage words in body, Non-Goals phrasing conforms, API catalog Name/Kind/Role only |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | spec passes phrasing/structure rules of docs/SPEC_STANDARD.md; features scoped text+unicode+inline; bytes/serde/wasm scoped out |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin oracle: inline unit tests in src/, must be lifted onto public surface only |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: dropped find_middle_snake/serde/bytes/deadline-timing tests; 2 raw-callback asserts rewritten onto declared guarantees (minimal script, capture_diff_slices) |
| 7 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: 33 upstream kept (snapshots inlined as assert_eq via reference probe), 58 generated on fresh inputs |
| 8 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(64) + integration(27 in 4 modules), depends_on.json, Cargo.lock pinned (similar 2.7.0, unicode-segmentation 1.12.0) |
| 9 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference run 91/91 pass (reference_score.json); spec_test_map.md, kept lists, taxonomy.jsonl, task.json written; lint fresh: LINT_PASS |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
