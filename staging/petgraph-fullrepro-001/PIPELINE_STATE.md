# Pipeline State — petgraph-fullrepro-001

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
oracle_count: 129
functions_in_scope: 378
functions_kept: 0
functions_excluded: 378
updated:    2026-08-25
```

todo:
- [x] rewrite_audit.md with per-file disposition (378 upstream fns, all excluded; generated-only)
- [x] oracle assembled: atomic (95) + integration (34 in 5 modules)
- [x] reference 129/129 (patched path + registry lock), depends_on 34/34
- [x] spec_test_map.md, taxonomy.jsonl, kept_nodeids.txt, task.json, reference_score.json
- [x] lint fresh on disk: LINT_PASS (negative control LINT_FAIL confirms sensitivity)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (27183 src LOC with scope_plan; six projections of one adjacency store; petgraph-specific index contracts; builds on 1.83 with indexmap =2.7.1 pin) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec drafting from docs.rs 0.8.3 within scope_plan |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec.md v1: 6-layer, 5 behavior sections (construction/mutation, indices+adjacency, stable+keyed, visitors+adapters, analysis, pathfinding+MST), state model, error table, 8 CVIs, import surface + API catalog; all contracts verified by probe against pinned 0.8.3 |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |
| 5 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: 112 in-crate fns all in out-of-scope modules; 142 external fns out-of-scope files; 124 in-scope external fns rely on out-of-scope imports at file level (Dot, dominators, iso, GraphError, IndexType, node_index helpers, visit traits, itertools/defmac); decision generated-only |
| 6 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: per-file disposition; fresh vocabularies; dummy-passable patterns avoided (Err assertions paired with positive siblings; property checks for multi-valid orders) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(95) + integration(34 in 5 modules: containers/traversal/scc_condensation/shortest_paths/spanning_convert), depends_on.json 34/34, Cargo.lock (registry petgraph 0.8.3; indexmap pinned =2.7.1 for cargo 1.83) |
| 8 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference 129/129 patched path AND registry-lock path (reference_score.json); 1 spec fix during dev: DFS child-exploration order corrected to reverse neighbor order (probe-verified, pre-oracle); 1 compile fix: connected_components needs compact indices so StableGraph comparison re-expressed via has_path_connecting; spec_test_map.md, taxonomy.jsonl, task.json written; lint fresh: LINT_PASS (negative control LINT_FAIL confirms sensitivity) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
