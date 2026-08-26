# Pipeline State — governor-fullrepro-001

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
updated:    2026-08-26
```

todo:
- [ ] 对每个 test 文件执行 import 分类（见 test-filter SKILL.md 表格）
- [ ] 标注每个文件的 import 类型

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (3687 LOC; GCRA rate-decision rule engine — one theoretical-arrival-time value per limiter projected through quota construction, direct/keyed decisions, NotUntil wait math, middleware snapshots, deterministic fake clock; v0.9.0 edition 2018 builds on scorer cargo 1.83; async/jitter surfaces scoped out) |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | CANDIDATES.md SELECTED row appended; begin spec drafting |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 landed; two probe rounds pinned: quota nanosecond-truncation laws (per_second(3) → 333333333ns, full-burst 999999999ns), decision laws (burst budget, exact-boundary conformance, batch weight math, capacity carrier value), NotUntil absolute-instant projection with pre-advanced clocks, wait_time_from zero clamping, snapshot rbc countdown/regain/idle-reset, quota round trips, retention threshold (equality evicts), store parity, FakeRelativeClock shared clones, Display strings; 25 validation checks + style gate pass |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
