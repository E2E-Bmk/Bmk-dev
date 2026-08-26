# Pipeline State — mvdansh-shell-syntax-fullrepro-001

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
updated:    2026-08-25
```

todo:
- [ ] 对每个 test 文件执行 import 分类（见 test-filter SKILL.md 表格）
- [ ] 标注每个文件的 import 类型

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-25 | S1_SCREENING | S1_SELECTED | all hard gates pass: in-scope LOC 9123 >= 3000; AST fact source with 7 public projections; upstream tests present (white-box mega-tables -> Track B expected); shell-standard saturation risk noted and mitigated by binding to v3.13.1 observables; scope_plan target_subdomain=syntax+typedjson, expected_oracle_max=170 |
| 2 | 2026-08-25 | S1_SELECTED | S2_SPEC_DRAFT | selection row recorded in staging/PROGRESS_go.md candidate log (CANDIDATES.md deferred; write scope is staging/ only) |
| 3 | 2026-08-25 | S2_SPEC_DRAFT | S2_SPEC_CHECK | spec v1 written from full API dump (216 exported decls) + 60 probe rounds against v3.13.1 (positions, error catalog, printer rules incl. minify case compression, quote failures, typedjson shape, variant gating, recovery, brace/simplify rewrites) |
| 4 | 2026-08-25 | S2_SPEC_CHECK | S2_SPEC_DONE | all 25 validation checks pass: phrasing fixes applied (no can/may outside quoted error texts, exact SpaceRedirects/Minify scope, backquoted error texts, table pipe escapes); 8 CVIs spanning parse/print/json/walk/quote/error domains; 7 behavior sections with narrative flow |
| 5 | 2026-08-25 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body ships without internal header (Definition A); zsh grammar + KeepPadding + DebugPrint declared out of scope in Non-Goals/import surface |
