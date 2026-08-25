# Pipeline State — textwrap-fullrepro-001

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
oracle_count: 111
functions_in_scope: 137
functions_kept: 0
functions_excluded: 137
updated:    2026-08-25
```

todo:
- [x] Stage 3 complete: oracle 111 tests (79 atomic / 32 integration), reference 111/111 both paths, LINT_PASS fresh

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (two wrapping algorithms behind one config engine, 3183 non-test LOC, 137 test fns, 8 public projections; 0.16.2 MSRV 1.70 builds on rustc 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec: probed reference (defaults, indent-on-empty-line, CR passthrough, fill_inplace last-space rule, Cow borrowing, wrap_columns arithmetic, penalty model) |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec.md v1: 6 behavior sections (wrap/fill, config, refill/indent, columns, text model, algorithms), 8 invariants, error table; 25 checks + style gate pass; smawk pinned =0.3.2 for toolchain 1.83 (noted for lock) |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |
| 5 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: 127/137 upstream fns are in-crate #[cfg(test)] mods (structurally unavailable); tests/indent.rs public but memorization-prone; version-numbers.rs excluded; decision generated-only |
| 6 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: per-file disposition; fresh vocabularies; dummy-passable patterns avoided (catch_unwind with positive check for zero-column panic) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(79) + integration(32 in 5 modules: pipeline/fill_refill/indent_dedent/columns_layout/consistency), depends_on.json 32/32, Cargo.lock (registry textwrap 0.16.2; smawk pinned =0.3.2 for cargo 1.83) |
| 8 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference 111/111 patched path AND registry-lock path (reference_score.json); 2 fixture fixes during dev: wrap fast-path bypasses Custom algorithm on fitting lines (re-fixtured below width); upstream wrap_columns debug-panics on overflowing cell with break_words=false (re-fixtured to algorithm pass-through); spec_test_map.md, taxonomy.jsonl, task.json written; lint fresh: LINT_PASS (negative control LINT_FAIL confirms sensitivity) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
