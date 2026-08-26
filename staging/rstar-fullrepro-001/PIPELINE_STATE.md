# Pipeline State — rstar-fullrepro-001

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
functions_in_scope: 49
functions_kept: 0
oracle_count: 91
updated:    2026-08-26
```

todo:
- [x] audit upstream test imports; rewrite_audit.md written (generated_only: inline #[cfg(test)] modules, crate-internal seeded-random utilities)
- [x] generated oracle built (76 atomic + 15 integration), taxonomy, kept_nodeids, depends_on.json
- [x] reference run 100% both modes (path patch 91/91, registry lock 91/91), LINT_PASS, spec_test_map, reference_score.json

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (4560 src LOC; R*-tree spatial index — one object multiset projected through population/envelope/metric/mutation/construction views; v0.12.2 manifest commit c8c5bf9, edition 2018, MSRV 1.63 builds on scorer cargo 1.83; v0.13.0 rejected for MSRV 1.85) |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | CANDIDATES.md SELECTED row appended; begin spec drafting |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 complete: 8 behavior sections + contract layer, all values probe-pinned over three probe rounds (AABB algebra, construction-path equivalence up to tie order, one-of-many removal, drain laziness, parameter panics, primitives forwarding); style gate + validation checks pass |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin test filtering (upstream tests are seeded-random `proptest`-style loops with internal APIs — expect generated_only) |
| 5 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | rewrite_audit.md complete: all 49 upstream #[test] fns are inline #[cfg(test)] modules importing crate::test_utilities (Hc128Rng seeded-random brute-force comparisons) or internal paths — 0 keepable, generated_only |
| 6 | 2026-08-26 | S3A_REWRITE | S3_ORACLE_MERGE | Track B oracle generated: 91 tests (76 atomic across aabb/construction/queries/neighbors/mutation/primitives/inspection, 15 integration workflows across mapping/collision/editing/custom); spec_test_map 91/91 covered; depends_on.json 15/15 integration annotated |
| 7 | 2026-08-26 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | path-patch run 91/91, registry-lock run 91/91 (Cargo.lock pins rstar 0.12.2 — fresh resolve picks 0.13.0 requiring rust 1.85 > toolchain 1.83); reference_score.json written |
| 8 | 2026-08-26 | S3_REFERENCE_RUN | S3_DONE | oracle_import_lint.py → LINT_PASS (fresh, newer than all oracle test files); task.json S3_DONE (91 base fns: 76 atomic / 15 integration, positive share 93% atomic) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
