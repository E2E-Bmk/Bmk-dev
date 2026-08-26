# Pipeline State — ropey-fullrepro-001

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
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (rope engine, 8328 non-test LOC, ~415 test fns scoped to expected_oracle_max=110, 8 public projections of one tree; v1.6.1 MSRV 1.65 builds on rustc 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | spec.md drafted from docs.rs 1.6.1 + crate root docs (6-layer): construction/io, metrics+conversions, reading, editing, slicing, line semantics, iterators, cmp/ord/hash |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: fixed Debug over-promise (chunk-layout dependent), chunk_at_line_break index rule, line accessor bound; leakage word "judgements" reworded; no can/may/should |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | spec passes SPEC_STANDARD phrasing/structure; doc(hidden) surface excluded; features pinned (default unicode_lines+simd) |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin oracle: ~334 inline unit tests + tests/ dir; drop MIN/MAX_BYTES-dependent, proptest, doc-hidden users |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: hidden-surface/randomized/private-module upstream tests excluded; decision generated-only (repetitive indexed variants consolidated, fresh fixtures for anti-memorization) |
| 7 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: per-file upstream disposition table; 2 spec_gap patches routed (empty-content chunks; end-position chunk-iterator line coord) |
| 8 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(58) + integration(33 in 5 modules), depends_on.json, Cargo.lock (registry ropey 1.6.1, smallvec 1.15.2, str_indices 0.4.4 — no pins needed on rustc 1.83) |
| 9 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference 91/91 both patched-path and registry-lock runs (reference_score.json); spec_test_map.md (generated_only header), kept lists, taxonomy.jsonl, task.json written; lint fresh: LINT_PASS |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
