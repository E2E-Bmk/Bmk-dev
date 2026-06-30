# SWE-E2E Benchmark — 任务构建工作台

这个仓库是 SWE-E2E benchmark 任务的主动开发工作台。我们从真实开源库出发，构建完整的多文件项目重建任务。

## 在开始之前

**先把 `skills/` 目录下的各个 SKILL.md 按顺序读一遍，不要跳过。** 整个流程的设计逻辑、每个阶段的判断标准、以及运行模型之前需要理解的所有前提，都在里面。

阅读顺序：

1. `skills/candidate-selector/SKILL.md` — 如何选择合适的候选库
2. `skills/spec-writer/SKILL.md` — 如何写行为规格说明
3. `skills/test-filter/SKILL.md` — 如何过滤和分类测试集
4. `skills/task-judge/SKILL.md` — 如何判断一个任务是否合格
5. `skills/task-synthesizer/SKILL.md` — 总调度：理解整条流水线

## 推荐工作流

用 Codex 或 Claude Code，以 `skills/task-synthesizer/SKILL.md` 作为主 skill 驱动任务合成。task-synthesizer 负责调度各阶段的子智能体，把它交给模型，观察输出即可。

```
Claude Code / Codex
└── 读 task-synthesizer/SKILL.md
    ├── Stage 1: candidate-selector
    ├── Stage 2: spec-writer
    ├── Stage 3: test-filter
    ├── Stage 4: candidate eval（cleanroom 隔离）
    └── Stage 5: task-judge
```

`wip/` 是活跃合成工作的目录，每个任务在这里经历完整流水线后，才能迁移到 `tasks/`。

## Human-in-the-Loop：你的核心职责

模型处理机械性工作，你负责判断。每个阶段产出之后，对照三条核心原则检查一遍再往下走：

**1. Like a developer（像开发者写的）**
spec 读起来像库的作者在给用户写文档，还是像一个 benchmark 评测框架？任何一句话像是写给评测者而非开发者的，打回去重写。

**2. Spec-driven（规格可追溯）**
每一条被保留的测试，都必须能指向 spec 里某个具体章节。测试找不到对应 spec 位置，要么 spec 有缺口，要么这条测试本身不该保留。

**3. Behavioral（测行为，不测内部实现）**
保留的测试检查的是任何正确实现都会产生的可观测行为，不是某个特定实现的内部字段名、repr 格式、或私有状态。

如果某个阶段的输出违反了某条原则，先定位问题出在哪个阶段：是这次模型的执行问题（打回重做），还是 skill 本身的指导需要改进（更新 SKILL.md）？把流程优化的洞察写进对应的 skill，而不是留在对话里。

## 目录结构

| 路径 | 说明 |
|---|---|
| `tasks/` | 已合格的 benchmark 任务（QUALIFIED），包含完整流水线产物供参考 |
| `wip/` | 进行中的任务候选 |
| `skills/` | 可复用的流程 skill |
| `harness/` | 评分脚本和运行工具 |
| `CANDIDATES.md` | 候选库选择与退出记录 |
| `weakness_table.md` | 各模型跨任务的能力弱点记录 |

外部依赖（不在本仓库中）：

- `../repo-pool/` — 克隆的源库，用于任务构建
- `../benchmarks/` — 外部 benchmark 参考
