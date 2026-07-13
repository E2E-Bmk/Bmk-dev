# SpecBench — 任务构建工作台

从真实开源 Python 库出发，构建"按行为规格重建完整项目"的评测任务。核心指标：Integration Gap = 单元通过率 − 集成通过率。

## 快速开始

1. 读 `REPO_STATUS.md` — 看哪些 repo 已完成、进行中、已退休
2. 读 `skills/task-synthesizer/SKILL.md` — 理解完整流水线
3. 看 `tasks/httpcore-transport-fullrepro-001/` — Golden Task 示例

## 目录结构

```
├── tasks/{task-id}/              # 已合格的 benchmark 任务（34 个）
│   ├── spec.md                   # 行为规格（模型唯一输入）
│   ├── task.json                 # 元数据（taxonomy、scorer 参数、得分）
│   ├── spec_test_map.md          # 测试↔spec 映射（审计用）
│   └── oracle/
│       ├── test_atomic.py        # 原子层测试
│       └── test_integration.py   # 集成+端到端测试
│
├── harness/                      # 评分脚本
│   ├── score_pytest_original.py  # pytest runner + 隔离
│   ├── run.py                    # cleanroom 执行入口
│   └── verify_task.py            # task 完整性校验
│
├── scripts/                      # 辅助工具
├── skills/                       # 流水线各阶段 SKILL 定义
│
├── REPO_STATUS.md                # 组员认领参考
├── CANDIDATES.md                 # 候选库选择/退休历史
└── AGENTS.md
```

本地还有（未提交）：`wip/`（流水线工作区）、`runs/`（评测记录）、`repo-pool/`（上游克隆）、`.envs/`（评分环境）

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

## 流水线

```
candidate-selector → spec-writer → test-filter → evaluation → task-judge
```

每个阶段对应 `skills/` 下的一个 SKILL.md。用 Codex / Claude Code 以 `skills/task-synthesizer/SKILL.md` 驱动。

## 核心原则

1. **Like a developer** — spec 读起来像库作者写的文档，不像 benchmark
2. **Spec-driven** — 每条测试可追溯到 spec 某个章节
3. **Behavioral** — 测试检查可观测行为，不检查内部实现

## 评分

```bash
# WSL 环境下
python harness/score_pytest_original.py \
  --source-repo wip/{task}/filter \
  --solution-dir <candidate_output> \
  --nodeids <nodeids_file> \
  --taxonomy <taxonomy_file> \
  --remove-path <pkg> \
  --timeout 300
```

模型可自由使用任何 PyPI 包。评分环境会安装模型声明的依赖后运行测试。
