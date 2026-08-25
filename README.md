# SpecBench — 任务构建工作台

从真实开源库（Python / Java / Rust / TypeScript）出发，构建"按行为规格重建完整项目"的评测任务。

## 快速开始

1. 读 `docs/REPO_STATUS.md` — 看哪些 repo 已完成、进行中、已退休
2. 读 `skills/task-synthesizer/SKILL.md` — 理解完整流水线
3. 看 `tasks/python/httpcore-transport-fullrepro-001/` — Golden Task 示例

## 目录结构

```
├── tasks/{lang}/{task-id}/       # 已合格的 benchmark 任务（python/java/rust/typescript）
│   ├── spec.md                   # 行为规格（模型唯一输入）
│   ├── task.json                 # 元数据（taxonomy、scorer 参数、得分）
│   ├── oracle/                   # 原子层 + 集成层测试
│   └── verdict.json              # 门禁裁定
│
├── harness/                      # 合成 / 验证 / 校验的全部脚本
│   ├── core/                     #   verify_task.py 校验、run.py 执行、verdict.py 裁定
│   ├── lang/{lang}/              #   语言特定 runner 与评分器
│   ├── runners/                  #   语言 runner 接口
│   ├── sandbox.py                #   Docker 评分沙箱（网络隔离、可复现）
│   └── evaluate.py               #   评测入口（--score-only 只校验；带 agent 需 LLM key）
│
├── agents/                       # agent 适配器（mini-swe-agent）
├── docker/                       # 镜像与 build_images.py
├── skills/                       # 流水线各阶段 SKILL 定义
├── docs/                         # SPEC_STANDARD.md / QUALITY_GATE.md / REPO_STATUS.md
├── requirements.txt              # 宿主侧依赖（含 mini-swe-agent）
├── CANDIDATES.md                 # 候选库选择
└── AGENTS.md
```


## Task 结构

每个 task 是自包含的：

```json
// task.json 示例
{
  "instance_id": "httpcore-transport-fullrepro-001",
  "status": "QUALIFIED",
  "oracle": {
    "test_files": ["oracle/test_atomic.py", "oracle/test_integration.py"],
    "count": 64,
    "scorer_isolation": ["--remove-path", "httpcore"]
  },
  "stats": { "atomic": 15, "integration": 35, "system_e2e": 14 },
  "reference_pass_rate": 1.0,
  "candidate_score": { "passed": 58, "total": 64 }
}
```

## 运行要求（自包含）

克隆后只要机器能构建 Docker，即可完成合成 / 验证 / 校验全流程。

- **验证**：`python harness/core/verify_task.py <task-id>` — 纯 Python，检查 task 结构与 spec-oracle 对齐，无需 Docker。
- **校验（评分）**：`python harness/evaluate.py --score-only --model <name> --tasks <id>` — 在 Docker 沙箱内跑 oracle 测试，网络隔离、可复现。首次运行前 `python docker/build_images.py` 构建镜像。
- **agent 评测**（可选）：同一入口去掉 `--score-only`，用 mini-swe-agent 让模型按 spec 重建仓库。需 `pip install -r requirements.txt` 并配置对应模型的 API key（见 `agents/config.json`）。

## 流水线

```
candidate-selector → spec-writer → test-filter → evaluation → task-judge
```

每个阶段对应 `skills/` 下的一个 SKILL.md。用 Codex / Claude Code 以 `skills/task-synthesizer/SKILL.md` 驱动。

## 核心原则

1. **Like a developer** — spec 读起来像库作者写的文档，不像 benchmark
2. **Spec-driven** — 每条测试可追溯到 spec 某个章节
3. **Behavioral** — 测试检查可观测行为，不检查内部实现
