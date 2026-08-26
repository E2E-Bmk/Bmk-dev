# Pipeline State — ojg-jsonpath-engine-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读参考，不在此复制）。
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

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | all hard gates pass: jp package 10916 src LOC >= 3000 (no generated code, zero external deps); path-expression fact source with >= 5 public projections (normalized string form, Get/First/Has/Locate selection, Set/Del/Remove/Modify mutation, Walk enumeration, PathMatch + filter Equation views); 159 upstream test funcs in 19 files, 18/19 external black-box (jp_test) but all carry module-level out-of-scope ojg imports (tt/oj/sen/alt/pretty/gen) -> Track B expected; JSONPath saturation risk mitigated by binding to pinned v1.28.5 observables (dialect diverges from RFC 9535; tag is 4 days old, post-cutoff); scope_plan target_subdomain=jp-over-native-go-data, expected_oracle_max=170 |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_DONE | spec v1 from go doc -all + README + 51 probe rounds vs pinned v1.28.5: 8 behavior sections, 8 CVIs, 25-row Error Semantics (exact texts incl. position-and-source parse errors and per-operation ending-fragment rules); dialect edges bound to pinned observables (wildcard spelling retention, descent rendering collapse and its reparse failure, existence-not-truthiness bare-path filters, null vs Nothing vs missing, case-insensitive struct field match, Del nil-holes vs Remove excision, Set auto-creation rules, map-order nondeterminism stated as unspecified); all 25 validation checks + style gate pass (escape-hatch word fixed, leakage greps clean) |
| 4 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body ships without internal header (Definition A); gen/streaming/procedures/custom-collections/struct-mutation declared out of scope in Non-Goals |
