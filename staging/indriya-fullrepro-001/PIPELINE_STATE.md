# Pipeline State — indriya-fullrepro-001

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 见 `skills/PIPELINE_STATE.template.md`（只读参考）。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S3_DONE
stage:      3
spec_iter:  1
filter_iter: 0
eval_iter:  0
updated:    2026-08-26
```

todo:
- [x] spec.md v2（probe-driven；两处 clause 收紧）
- [x] oracle 106 tests（80 atomic / 26 integration），mvn -o test 全绿
- [x] filter artifacts（spec_test_map / kept_nodeids / taxonomy / rewrite_audit / lint_result=LINT_PASS）
- [x] verify_task STATIC_VALID
- [ ] Docker dummy gate（PENDING — no Docker on this VM）
- [ ] Docker reference run（PENDING — no Docker on this VM）

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (18581 non-blank main LOC, 928 upstream test methods) |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | CANDIDATES.md SELECTED row appended |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S3_ORACLE_BUILD | spec.md drafted after 2 probe rounds (construction/arithmetic/units/conversion/comparison/scales/format) |
| 4 | 2026-08-26 | S3_ORACLE_BUILD | S3_DONE | 106 tests (80 atomic / 26 integration) green vs pinned 2.2; probes 3–5 pinned exact renderings + entry-point divergence; spec v2 tightened 2 clauses (same-unit division cancellation, unit round-trip scope); lint LINT_PASS; verify STATIC_VALID; Docker gates PENDING |

---

## Docker-pending gates (this VM has no Docker)

- `S3A_DUMMY` / `S3B_DUMMY`（真实 Docker dummy run via `harness/lang/java/score_java.py`）: **PENDING — Docker unavailable**
- `S3_REFERENCE_RUN` official gate（`score_java.py --reference`, 100%）: **PENDING — Docker unavailable**
- Non-Docker substitute used instead: local `mvn test -Dcandidate.version={pinned}`
  against the pinned Maven Central reference artifact, recorded in
  `filter/local_reference_run.txt`; requirement 100%.

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 generated `.java` tests 至少一个存在
- `S4_SETUP` 要求 `filter/lint_result.txt` 存在且首行为 `LINT_PASS`
- `S4_SETUP` 要求 Docker reference gate = 100%（当前 PENDING）
- `QUALIFIED` 要求 `filter/lint_result.txt` 的时间戳晚于 `oracle/` 下所有测试文件的最后修改时间
