# Pipeline State — snakeyaml-engine-fullrepro-001

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
spec_iter:  0
filter_iter: 0
eval_iter:  0
updated:    2026-08-26
```

todo:
- [x] spec.md（6-layer，internal header 拆到 spec_internal.md；scope=Load/Dump/Compose + settings）
- [x] oracle/ Maven packet（pom.xml + 66 atomic + 27 integration + support）
- [x] 本地 reference run 100%（93/93，`filter/local_reference_run.txt`）
- [x] `filter/lint_result.txt` 首行 LINT_PASS
- [x] `filter/spec_test_map.md` + `kept_nodeids.txt` + `taxonomy.jsonl` + `rewrite_audit.md`
- [x] task.json（language=java，stats 66/27/0，taxonomy 93 keys）
- [x] `verify_task.py` → STATIC_VALID
- [ ] Docker dummy gate（PENDING — Docker unavailable）
- [ ] Docker reference gate（PENDING — Docker unavailable）

---

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes.md complete; decision=keep (14759 non-blank main LOC, 420 upstream test methods) |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | CANDIDATES.md SELECTED row appended |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S3_ORACLE | spec.md written from four probe rounds against the pinned 2.9 artifact; internal header in spec_internal.md |
| 4 | 2026-08-26 | S3_ORACLE | S3_DONE | generated-only oracle 93 tests (66 atomic / 27 integration); local mvn reference 93/93 first run; LINT_PASS (isPresent phrasing fixed); STATIC_VALID; Docker gates PENDING |

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
