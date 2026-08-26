# Pipeline State — pubgrub-fullrepro-001

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
functions_in_scope: 32
updated:    2026-08-25
```

todo:
- [ ] audit upstream tests: imports, feature gates, fixture styles
- [ ] write filter/rewrite_audit.md with per-file disposition
- [ ] decide kept_upstream vs generated_only

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (4228 LOC; conflict-driven version solver with derivation-tree failure proofs and documented English reporting; v0.3.0 pinned — 0.3.1+ needs edition2024, scorer runs cargo 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | begin spec drafting |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 landed; three probe rounds fixed: Ranges display grammar (nine segment forms, ∅/*/" | "), touching-segment union merge vs discrete-gap retention, from_iter normalization skipping invalid pairs, simplify's three fixed rules, offline provider strategy (highest contained version; no-match packages outrank all; conflicts then fewest-candidates), unavailability message string, deterministic solving incl. cycles/self-deps/backtracking, unknown-root NoVersions tree, collapse merge sides, all External sentence forms, format_terms five shapes with pos/neg normalization, Because/And-because chaining with " ({n})" refs and blank-line separation, all PubGrubError and VersionParseError Display strings; 25 validation checks + style gate pass |
| 4 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | proceed to oracle import audit |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
