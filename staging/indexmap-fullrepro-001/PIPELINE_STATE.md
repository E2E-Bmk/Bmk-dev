# Pipeline State — indexmap-fullrepro-001

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
functions_in_scope: 72
functions_kept: 0
oracle_count: 121
updated:    2026-08-26
```

todo:
- [x] audit upstream test imports; write rewrite_audit.md (generated_only: inline #[cfg(test)] modules + quickcheck harness)
- [x] build generated oracle (atomic + integration workspaces), taxonomy, kept_nodeids
- [x] reference run 100% (path patch + registry lock), lint LINT_PASS, spec_test_map, reference_score.json

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (order-preserving map/set as rule engine over one entry sequence + hash index, six public projections; pinned 2.7.1 @ 42e57a3, MSRV 1.63 fits cargo 1.83 and matches transitive pins in sibling packets; inline upstream tests → generated_only expected) |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | CANDIDATES.md SELECTED row appended; begin probe rounds + spec drafting |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 complete: 9 behavior sections + contract layer, all values probe-pinned over three probe rounds (swap/shift laws, insert_before/shift_insert boundaries, splice collision law, set identity laws, algebra order, slice value semantics, panic table); style gate + validation checks pass |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin test filtering (upstream tests are inline #[cfg(test)] modules + quickcheck harness — expect generated_only) |
| 5 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | rewrite_audit.md complete: all 72 upstream #[test] fns live in inline #[cfg(test)] modules (crate-internal paths, feature-gated files, quickcheck/fnv dev-deps) — 0 keepable, generated_only |
| 6 | 2026-08-26 | S3A_REWRITE | S3_ORACLE_MERGE | Track B oracle generated: 121 tests (106 atomic across construction/lookup/removal/reorder/bulk/sorting/slices/entry/set_basic/set_algebra/iteration, 15 integration workflows across registry/aggregation/dedupe/editing); spec_test_map 121/121 covered; depends_on.json 15/15 integration annotated |
| 7 | 2026-08-26 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | path-patch run 121/121, registry-lock run 121/121 (Cargo.lock pins indexmap 2.7.1 + hashbrown 0.15.5 — fresh resolve picks indexmap 2.14.0 requiring rust 1.85 > toolchain 1.83); reference_score.json written |
| 8 | 2026-08-26 | S3_REFERENCE_RUN | S3_DONE | oracle_import_lint.py → LINT_PASS (fresh, newer than all oracle test files); task.json S3_DONE (121 base fns: 106 atomic / 15 integration, positive share 93% atomic) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
