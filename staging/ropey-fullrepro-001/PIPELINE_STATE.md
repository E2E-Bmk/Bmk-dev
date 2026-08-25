# Pipeline State — ropey-fullrepro-001

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
- [ ] audit upstream test imports against spec surface; rewrite or drop undeclared-surface asserts (doc(hidden) items: MAX_BYTES/MIN_BYTES/MAX_CHILDREN/MIN_CHILDREN, Lines::from_str_pt, assert_integrity/assert_invariants, RopeBuilder::_append_chunk/_finish_no_fix)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (rope engine, 8328 non-test LOC, ~415 test fns scoped to expected_oracle_max=110, 8 public projections of one tree; v1.6.1 MSRV 1.65 builds on rustc 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | spec.md drafted from docs.rs 1.6.1 + crate root docs (6-layer): construction/io, metrics+conversions, reading, editing, slicing, line semantics, iterators, cmp/ord/hash |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: fixed Debug over-promise (chunk-layout dependent), chunk_at_line_break index rule, line accessor bound; leakage word "judgements" reworded; no can/may/should |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | spec passes SPEC_STANDARD phrasing/structure; doc(hidden) surface excluded; features pinned (default unicode_lines+simd) |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin oracle: ~334 inline unit tests + tests/ dir; drop MIN/MAX_BYTES-dependent, proptest, doc-hidden users |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
