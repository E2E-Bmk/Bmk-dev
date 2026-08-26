# Pipeline State — rrule-fullrepro-001

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
functions_in_scope: 317
functions_kept: 0
functions_excluded: 317
oracle_count: 97
updated:    2026-08-25
```

todo: (S3 complete; next stage owner picks up at S4_SETUP)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (~9000 non-test LOC; RFC 5545 recurrence engine with four projections of one property model; builds on cargo 1.83, MSRV 1.74) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec drafting |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 landed; three probe rounds fixed: UNTIL-must-be-UTC (same-zone rejected), BYMONTHDAY zero pruning, negative-monthday getter/Display invisibility, parse-vs-builder range error split, limited-flag on exact cap, duplicate-preserving merge, instant-based exdate, DST gap +1h shift, fall-back earlier offset; floating datetimes + Tz::LOCAL scoped out (host-dependent); 25 validation checks + style gate pass |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |
| 5 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit done: all 317 upstream tests in-crate (crate:: imports, pub(crate) helpers, private parser/validator types) — structurally unavailable; serde.rs + exrule-touching regression tests also feature-gated out of scope; decision generated-only |
| 6 | 2026-08-25 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md landed: per-file disposition; fresh 2026-2028 fixtures replace memorization-prone 1997 dateutil dates; dummy-passable patterns avoided (error tests paired with positive siblings; streams asserted as full DateTime vectors) |
| 7 | 2026-08-25 | S3B_TRIGGER | S3_ORACLE_MERGE | oracle assembled: workspace + atomic(64) + integration(33 in 5 modules: round_trip/streams/selection/zones/errors_validation), depends_on.json 33/33, Cargo.lock (registry rrule 0.14.0, chrono 0.4.45, chrono-tz 0.10.4 — clean on cargo 1.83, no pins) |
| 8 | 2026-08-25 | S3_ORACLE_MERGE | S3_DONE | reference 97/97 on patched path AND registry lock, first run both (all uncertain contracts probe-verified pre-authoring); spec_test_map.md, taxonomy.jsonl, kept_nodeids.txt, task.json written; lint fresh: LINT_PASS (negative control LINT_FAIL on undeclared GrammarInternals confirms sensitivity) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
