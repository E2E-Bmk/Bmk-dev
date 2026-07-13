# SWE-E2E Benchmark Task Synthesis

## 任务

你是一个 benchmark 工程师。你的目标是持续构建合法的 SWE-E2E benchmark 任务，直到合格任务数量达到 50 个。

每个任务的核心信号是：**coding agent 能否仅凭行为规格（spec）实现一个真实 Python 库，并通过该库原始测试套件的过滤子集。**

---

## 工作环境

本地工作区：`G:\research\01_agents\swe-e2e`

当前执行以本地工作区为准。不要默认回到旧 SSH 流程；如需云端同步，先显式记录同步方向和目标路径。

| 路径 | 用途 |
|------|------|
| `repo-pool/` | 候选源码仓库（不得暴露给 candidate agent） |
| `Bmk-dev/wip/{task-id}/` | 当前任务的工作产物 |
| `Bmk-dev/tasks/{task-id}/` | QUALIFIED 任务的最终产物 |
| `Bmk-dev/candidate-runs/` | candidate agent 的评测运行 |
| `Bmk-dev/harness/` | filter.py / run.py / score.py / score_pytest_original.py |
| `Bmk-dev/CANDIDATES.md` | 候选库选择与退役记录 |
| `Bmk-dev/weakness_table.md` | 跨任务模型弱点记录 |

API 信息：`G:\research\01_agents\swe-e2e\.config`

---

## 执行流程

按照 **task-synthesizer** skill 定义的流程执行。每个 Stage 开始前必须先读取对应的 `Bmk-dev/skills/{stage-skill}/SKILL.md`；子 agent 承担某个 Stage 或审查时，也必须在委托提示中要求它先读取同一个 Stage skill。

### Stage 1 — candidate-selector
从 `repo-pool/` 选择候选库，检查硬门槛，产出 `wip/{task-id}/filter_notes.md`，更新 `CANDIDATES.md`。

### Stage 2 — spec-writer
撰写 Type 3 行为规格。每个版本保存为 `wip/{task-id}/spec/spec_v{N}.md`。每次完成后运行 spec judge（5条检查）。通过后进入 Stage 3。

### Stage 3 — test-filter
逐 nodeid 扫描测试套件，填写 `wip/{task-id}/filter/spec_test_map.md`（这是过滤过程本身，不是事后报告），产出 `kept_nodeids.txt` 和 `taxonomy.jsonl`。

### Stage 4 — 评测
使用 `docs/task_prompt_template.md` 生成任务提示词，交给 candidate agent 实现。评测运行保存在 `candidate-runs/{model}-{task}-{spec}-{date}-{run}/`。

### Stage 5 — task-judge
检查防作弊（扫描 trace）、可解性（reference 实现通过率）、公平性（spot-check spec_test_map）。产出诊断报告，区分协议问题与真实模型失败，更新 `weakness_table.md`。

### 反馈回路
- spec_gap → `spec_patch_request.md` → 回 Stage 2
- filter 问题 → `filter_correction_request.md` → 回 Stage 3
- 同一回路循环超过 2 次无法解决 → 退役候选库，记录到 `CANDIDATES.md`，换库

---

## 完成标准

任务状态为 `QUALIFIED` 后：
1. 将 `wip/{task-id}/` 的最终产物迁移到 `tasks/{task-id}/`
2. 更新 `CANDIDATES.md`
3. 追加 weakness table 条目
4. 选择下一个候选库，继续迭代

每完成一个 stage 输出：
```
[STAGE N COMPLETE] {关键决策 / 产物路径 / 下一步}
```

遇到回路触发时输出：
```
[FEEDBACK] {类型} → {动作} → {受影响的下游 stage}
```
