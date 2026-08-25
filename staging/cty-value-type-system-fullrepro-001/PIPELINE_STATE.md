# Pipeline State — cty-value-type-system-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `dev/skills/PIPELINE_STATE.template.md`（只读）。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 1
eval_iter:  0
language:   go
updated:    2026-08-25
```

todo: (none — packet complete)

functions_in_scope: 83 (upstream Test funcs in cty+convert+json+msgpack)
functions_kept: 0 (Track A)
functions_excluded: 83
generated_tests: 132 (96 atomic + 36 integration)

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | hard gates pass: in-scope 11776 LOC, 5 projections over one value/type fact source, deterministic table-driven suite; scope_plan excludes function/stdlib+gocty; v1.19.0 (2026-07-06) post-cutoff |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | filter_notes.md recorded; entering spec drafting with probe rounds |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | 5 probe rounds against pinned v1.19.0: equality ladder incl. refined-notnull unknown bools, number precision (0.1+0.2==0.3 parsed), div/mod-by-zero, set HasIndex panic (docs mismatch), marks propagation/flattening, refinement builder panics + known-answer ops, convert matrix incl. list->tuple unavailable, json/msgpack round trips + error texts |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | 25-check pass: modal phrasing scrubbed (can/could), Non-Goals phrasing conformant, API catalogs as Name/Kind/Role, 7 CVIs, 9 behavior sections; capsule/function/gocty/gob in Non-Goals |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | entering upstream test audit |
| 6 | 2026-08-25 | S3A_IMPORT_AUDIT | S3B_TRIGGER | 81/83 upstream funcs are in-package white-box (compile inside target pkgs), 2 external funcs are repr-golden path renderers; 100% discard -> Track B early trigger; rewrite_audit.md on disk |
| 7 | 2026-08-25 | S3B_TRIGGER | S3B_GENERATE | targets enumerated from spec sections (9 behavior sections, error table, 7 CVIs, 2 workflows) |
| 8 | 2026-08-25 | S3B_GENERATE | S3B_REFERENCE | 132 tests written (96 atomic + 36 integration); ref-run fix: HasWhollyKnownType spec wording corrected to observed v1.19.0 (empty collection of dynamic element type contains no dynamic unknowns → true); Go 1.25 toolchain required by module |
| 9 | 2026-08-25 | S3B_REFERENCE | S3B_DUMMY | reference 132/132 vs pinned v1.19.0 (also re-verified against published proxy module, no replace) |
| 10 | 2026-08-25 | S3B_DUMMY | S3B_DUMMY | filter_iter=1: accept-all stub passed 20/132 (15.2%) — round-trip/identity tests bound only to Equals/RawEquals; strengthened with negative equality controls + native-content assertions (AsString/AsBigFloat/IsNull/LengthInt/marshaled bytes); reference re-verified 132/132 |
| 11 | 2026-08-25 | S3B_DUMMY | S3_DONE | per-test dummy runs (panic isolation): accept-all 6/132 (4.5%), reject-all 2/132 (1.5%) — PASS; lint symbol check verified live (injected UndeclaredBogusSymbol → LINT_FAIL at file::129), final LINT_PASS on disk; go.sum generated from proxy; task.json/kept_nodeids/taxonomy/spec_test_map recorded |

---

## Go Catalogue Overrides（language=go，本批次适用）

- 构建 oracle 位于 `oracle/{atomic,integration}/*_test.go` + `oracle/go.mod`
  （module `{task}-oracle`，require target；评分时由 runner 注入 `replace`）。
- 测试 ID 形如 `atomic::TestName` / `integration::TestName`。
- dummy gate：同一 module path 的对抗性 stub 模块，`go mod edit -replace` 后
  运行完整 oracle，要求 <=10% 通过。
- reference gate：pinned upstream checkout `replace` 后运行完整 oracle，
  要求 100% 通过，结果落盘 `filter/reference_score.json`。
- lint：Go-enabled `oracle_import_lint.py` + 本任务 TARGET_IMPORTS 条目，
  输出落盘 `filter/lint_result.txt`，首行必须 `LINT_PASS`，时间戳晚于 oracle。
