# Pipeline State — ignore-fullrepro-001

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
functions_in_scope: 61
functions_kept: 0
functions_excluded: 61
oracle_count: 106
updated:    2026-08-25
```

todo:
- [x] Stage 3 complete; packet ready for Stage 4 setup

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (4808 non-test LOC; precedence rule engine projected through matcher queries and real walks; builds on cargo 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec drafting |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec.md v1: 6-layer, 5 behavior sections (pattern matching, overrides, types, walking, parallel walking), state model, error table, 8 CVIs; dialect+precedence contracts verified by two probe rounds against pinned 0.4.23 |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |
| 5 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: 56 in-crate fns structurally unavailable (super::/crate:: + private TempDir; dir.rs targets private module; git-config + symlink fns out of scope); 5 external fns depend on upstream fixture file + should_panic message text; decision generated-only |
| 6 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: per-file disposition; fresh vocabularies; dummy-passable patterns avoided (None verdicts paired with positive siblings; walks assert exact sorted path sets) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(75) + integration(31 in 5 modules: precedence/matcher_walk/override_types/parallel/limits_sorting), depends_on.json 31/31, Cargo.lock (registry ignore 0.4.23; ignore =0.4.23 + globset =0.4.15 pinned for cargo 1.83) |
| 8 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference 106/106 patched path AND registry-lock path (reference_score.json); 3 spec fixes during dev, all probe/source-verified pre-final: add_def segment-count parsing, types blanket-Ignore requires a positive selection, clear removes the definition (not marks); 1 composition fix: decisive override verdict is final and bypasses ignore files + types (spec Source precedence rewritten, probe-verified); spec_test_map.md, taxonomy.jsonl, task.json written; lint fresh: LINT_PASS (negative control LINT_FAIL on undeclared GlobInner confirms sensitivity) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
