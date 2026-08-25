# Pipeline State — fst-fullrepro-001

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
- [ ] audit upstream test imports against spec surface; excluded surface: Node/Transition/CompiledAddr, search_with_state/StreamWithState, get_key_into, map_data, new_type/fst_type, quickcheck properties

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (FST engine, 6425 non-test LOC, 7 in-scope projections of one byte image; levenshtein feature scoped out; builds on rustc 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | spec.md drafted from docs.rs 0.4.7 (6-layer): build ordering contract, queries, streams/ranges, automaton search, set-op lattice, raw/bytes, error taxonomy |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: no modal verbs, no leakage words; Non-Goals phrasing conforms; API catalog Name/Kind/Role only; scoped-out surface excluded from Import Surface |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | spec passes SPEC_STANDARD phrasing/structure; no features required; WrongType documented as reserved |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | begin oracle: tests/test.rs public-path tests keepable; raw/tests.rs mixes private helpers — per-function extraction |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
