---
name: task-synthesizer
description: "Orchestrate the full SWE-E2E benchmark task synthesis pipeline: candidate selection -> spec writing -> test filtering -> evaluation -> judging. Use when constructing a new benchmark task from scratch, resuming a pipeline run, or routing feedback between stages. This is the top-level coordinator - each stage delegates to its specialist skill."
---

# Task Synthesizer

## State Machine

每个任务在 `wip/{task}/PIPELINE_STATE.md` 维护一个运行中的状态机实例。

**Stage 1 开始前（新任务）：** 从 `wip/_template/PIPELINE_STATE.md` 复制到 `wip/{task}/PIPELINE_STATE.md`，替换 `{TASK_ID}` 和 `{DATE}`。

**每次分派子 agent 前：** 读 `PIPELINE_STATE.md`，确认 `state` 与即将运行的 stage 匹配。不匹配 → 不分派，先解决状态不一致。

**每次子 agent 返回后：** 检查 `PIPELINE_STATE.md` 是否已更新（state 已转移，History 已追加）。未更新 → 子 agent 未正确退出，视为失败，重新运行。

**循环终止：** `spec_iter > 2`、`filter_iter > 2` 或 `eval_iter > 2` 且未解决 → 直接设 `state → RETIRED`，不再继续循环。

---

## Core Principles

These three principles are the main thread's judgment criteria. Every subagent output is reviewed against them before the pipeline proceeds.

**1. Like a developer** — The spec must read like documentation written by the library author, not a benchmark artifact. No task IDs, no evaluation apparatus, no audit language in the candidate-visible body. If it reads like a test harness, reject it.

**2. Spec-driven** — Every kept test must be traceable to a specific spec section. Every judge verdict must reference spec coverage. If a test cannot be mapped to the spec, or a failure cannot be explained by a spec gap, it is a verifier problem, not a model problem.

**3. Behavioral** — Tests check observable outcomes that any correct reimplementation would produce. Failures must reflect genuine capability gaps, not protocol artifacts (exact strings, internal names, fixture shapes). If failures cluster around undocumented internal shapes, the instrument is broken.

## Orchestrator Role

The main thread dispatches subagents for execution tasks (spec writing, test filtering, evaluation, judging). The main thread does not execute these itself — it monitors, reviews output against the three principles, and intervenes when necessary.

**When to accept:** subagent output satisfies all three principles applicable to that stage.

**When to return for correction:** output violates a principle but the fix is within the subagent's scope (spec language is not developer-like, a test has no spec_section mapping, a judge skipped the preflight).

**When to intervene directly:** the subagent has looped more than twice on the same issue without resolution, or the root cause requires a pipeline-level decision (retire the candidate, restructure the spec, change the filter strategy).

## Skill Discipline

Before starting any pipeline stage, read the specialist skill named for that stage from this workspace's `Bmk-dev/skills/{skill-name}/SKILL.md`. Treat that file as the stage authority. This is a mandatory pre-flight check, not optional background context.

- Stage 1 must read `Bmk-dev/skills/candidate-selector/SKILL.md`.
- Stage 2 must read `Bmk-dev/skills/spec-writer/SKILL.md`.
- Stage 3 must read `Bmk-dev/skills/test-filter/SKILL.md`.
- Stage 4 must give the candidate agent only the public packet/run prompt; do not give it workflow skills, source repositories, tests, score reports, or previous attempts.
- Stage 5 must read `Bmk-dev/skills/task-judge/SKILL.md`.

When delegating a stage or stage audit to a subagent, instruct the subagent to read the same stage skill before inspecting task artifacts. The delegation prompt must name the exact `Bmk-dev/skills/{skill-name}/SKILL.md` path to read first.

Do not use deprecated root-level SWE-E2E skills, archived v1 workflow skills, or unrelated global skills for this pipeline. The workflow authority is this `Bmk-dev/skills/` tree plus the objective file.

## Workspace Layout

```
Bmk-dev/
|-- wip/{task-id}/               <- active synthesis work
|   |-- filter_notes.md          <- candidate-selector output
|   |-- spec/
|   |   |-- spec_v{N}.md
|   |   `-- spec_patch_request.md
|   |-- filter/
|   |   |-- spec_test_map.md
|   |   |-- kept_nodeids.txt
|   |   |-- taxonomy.jsonl
|   |   `-- filter_correction_request.md
|   `-- judge/
|       `-- diagnosis_report.md
|-- tasks/{task-id}/             <- QUALIFIED tasks (graduated from wip/)
|   |-- spec.md
|   |-- kept_nodeids.txt
|   |-- taxonomy.jsonl
|   `-- spec_test_map.md
|-- candidate-runs/              <- evaluation runs
|   `-- {model}-{task}-{spec}-{date}-{run}/
|       |-- task_prompt.txt
|       |-- output/
|       `-- score_report.md
|-- skills/                      <- active stage SKILL.md files only
|-- archive/deprecated-skills/   <- old workflow skills and packaged snapshots
|-- CANDIDATES.md                <- selection + retirement log
`-- weakness_table.md            <- cross-task model weakness log
```

All stages write to `wip/{task-id}/` under their designated subdirectory. Do not write to `tasks/` directly - only the orchestrator moves a task there upon QUALIFIED.

---

## Pipeline Stages

```
candidate-selector -> spec-writer -> test-filter -> [evaluation] -> task-judge
       ↑                 ↑              ↑                              |
       `--- retire ------┴-- spec gap --┴-- filter issue -------------┘
```

| Stage | Skill | Key Output |
|-------|-------|-----------|
| 1. Select candidate | `candidate-selector` | `filter_notes.md`, CANDIDATES.md entry |
| 2. Write spec | `spec-writer` | `spec_vN.md` (validated) |
| 3. Filter tests | `test-filter` | `spec_test_map.md`, `kept_nodeids.txt`, `taxonomy.jsonl` |
| 4. Evaluate | _(run candidate agent with spec only)_ | agent trajectory, score |
| 5. Judge | `task-judge` | task status, diagnosis report, weakness table entry |

---

## Stage Handoffs

### After candidate-selector
- Pass: proceed to spec-writer with repo path and filter_notes.md
- Fail hard gate: record retirement in CANDIDATES.md, select new candidate

### After spec-writer

Review against principles 1 and 2 before proceeding:
- **Principle 1 check**: Read the spec body. Does it read like developer documentation, or like a benchmark artifact? Any sentence that sounds like it was written for an evaluator → return to spec-writer.
- **Principle 2 check**: Is every item in the spec traceable to public API surface? Is source_boundary in the internal header non-empty (proof that sources were actually read)?
- All 5 validation checks pass: proceed to test-filter
- Any check fails: patch spec, re-validate before proceeding

**Candidate packet assembly**: the candidate receives the spec body only. Strip the `<!-- INTERNAL ... -->` header before assembling the run prompt. The candidate must not see task_id, delta notes, or source_boundary.

### After test-filter

Review against principles 2 and 3 before proceeding:
- **Principle 2 check**: Sample `covered` rows from spec_test_map.md. Does each `spec_section` value match a real heading in the spec file? If not, the map was produced without genuine spec mapping — return to test-filter.
- **Principle 3 check**: Sample kept tests. Do they check observable behavior, or internal shapes? If a significant share checks repr format, field names, or exact error message text → return to test-filter.
- spec_gap rows present: issue `spec_patch_request.md` → route to spec-writer → after patch, rerun Stage 3
- Track A + Track B combined oracle < 30 nodeids: record retirement, return to candidate-selector
- Oracle built: proceed to evaluation
- If `filter/oracle_source: generated_only` in spec_test_map.md: flag for task-judge additional spot-check

### After evaluation
- Always proceed to task-judge
- If run was interrupted or environment anomaly detected: note in diagnosis, re-run if needed

### After task-judge

Before accepting any verdict, verify diagnosis report structural validity:
- Does the report contain a **Preflight output** block with the literal `__file__` path? If absent → report is invalid, return to task-judge.

| Status | Action |
|--------|--------|
| `CHEAT_DETECTED` | Invalidate run, fix evaluation environment, re-evaluate |
| `BROKEN` (solvability) | Fix environment or return to test-filter; re-evaluate |
| `BROKEN` (fairness) | Process `filter_correction_request.md` via test-filter; re-evaluate |
| `BROKEN` (spec gap) | Process `spec_patch_request.md` via spec-writer → test-filter → re-evaluate |
| `QUALIFIED` | Record in CANDIDATES.md, append to weakness table, done |

---

## Feedback Artifacts

When task-judge signals a problem, it produces one of:

`spec_patch_request.md` - list of spec gaps with evidence; hand to spec-writer

`filter_correction_request.md` - list of misclassified or incorrectly kept tests; hand to test-filter

The stage that receives the request processes it, updates its outputs, and signals back to the orchestrator. The orchestrator then re-runs all downstream stages.

---

## Loop Termination

A feedback loop terminates when:
- The requested artifact is updated and all downstream checks pass, or
- The root cause is determined to require candidate retirement

Cycles through the same loop more than twice without resolution -> retire candidate.

---

## Completion Record

When a task reaches `QUALIFIED`, append to `CANDIDATES.md`:

```
| {repo} | QUALIFIED | spec_v{N} | {preserved_rate} | {reference_rate} | {date} |
```

And add weakness table entries for all real model failures found during judging.
