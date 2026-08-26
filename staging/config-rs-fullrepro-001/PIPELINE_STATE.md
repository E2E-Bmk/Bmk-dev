# Pipeline State — config-rs-fullrepro-001

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
- [x] Stage 1–3 packet complete; awaiting Stage 4 (candidate evaluation) outside this deliverable

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (layered-config rule engine, 4887 LOC, 154 test fns, clean imports, docs aligned; pinned v0.15.20 for MSRV 1.76 <= sandbox rustc 1.83) |
| 2 | 2026-08-25 | S1_SELECTED | S1_SELECTED | version re-pin: v0.15.20's toml stack pulls edition2024 crates rustc 1.83 cannot build; re-pinned to v0.15.11 (532ab4d, edition 2018, toml 0.8) with Cargo.lock pins indexmap 2.7.1 / hashbrown 0.15.5; filter_notes.md updated |
| 3 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | spec.md drafted from README + docs.rs surface + reference behavior (6-layer structure): builder/sources/merge, env pipeline, path grammar, typed access, deserialization, errors |
| 4 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | self-check: modal phrasing, all oracle-referenced symbols declared in API catalog (Config, ConfigBuilder, File, FileFormat, Environment, Value, ValueKind, ConfigError, Source, Map) |
| 5 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | spec passes phrasing/structure rules of docs/SPEC_STANDARD.md |
| 6 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | upstream testsuite imports only crate-root re-exports; excluded suites (async, json5/yaml/ron, ser, legacy) noted in rewrite_audit.md |
| 7 | 2026-08-25 | S3A_IMPORT_AUDIT | S3A_REWRITE | snapbox message asserts → ConfigError variant/field checks; temp_env process-env mutation → Environment::source(Some(map)); #[should_panic] → Result asserts; disk fixtures → File::from_str literals |
| 8 | 2026-08-25 | S3A_REWRITE | S3A_FAIRNESS | identifier audit vs spec vocabulary: remaining flags are test names/locals/serde attrs only |
| 9 | 2026-08-25 | S3A_FAIRNESS | S3A_DUMMY | static audit: every test asserts values/variants through config entry points; no #[should_panic] |
| 10 | 2026-08-25 | S3A_DUMMY | S3A_DONE | kept 68 upstream-derived tests (31 atomic + 37 integration) |
| 11 | 2026-08-25 | S3A_DONE | S3_ORACLE_MERGE | +14 generated tests (8 atomic typed-access/env-gap, 6 integration cross-view invariants); spec_test_map.md + depends_on.json written |
| 12 | 2026-08-25 | S3_ORACLE_MERGE | S3_REFERENCE_RUN | lint_result.txt = LINT_PASS (fresh, after last oracle edit) |
| 13 | 2026-08-25 | S3_REFERENCE_RUN | S3_DONE | reference 532ab4d (v0.15.11) passes 82/82 via patched workspace (reference_score.json) |

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests` 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
