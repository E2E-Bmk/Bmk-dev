# E2ECodeBench AAAI 实验计划

> 日期：2026-07-12
> DDL：2026-07-28（16 天）
> 状态：规划中

---

## 核心立意

现有 repo 级 benchmark（NL2RepoBench 等）通过提供蓝图级规格，将 repo 生成退化为并行的函数级翻译。E2ECodeBench 只提供行为级规格，首次隔离并量化 LLM **自主进行跨模块系统集成**的能力。

核心指标：**Integration Gap** = Unit Pass Rate − Integration Pass Rate

关键设计决策：
- 测试套件已改写为检测行为而非检测接口，模型无需猜测命名
- Spec 只提供 test-interface contract（测试会调用的公共入口），不提供内部架构

---

## 预期 Reviewer 攻击与防线

| 攻击 | 防线 | 对应实验 |
|------|------|----------|
| NL2RepoBench 已经做了 repo 级生成 | 他们给蓝图（1300 行含全部签名+示例+edge case），我们给行为规格（~1000 词）；他们测翻译能力，我们测设计+集成能力 | 实验 4（消融） |
| Integration Gap 可能只反映测试难度 | 失败模式分类证明 gap 来自跨模块交互失败 | 实验 2（分类） |
| 模型失败可能是 spec 信息不足 | 人类基线在同样 spec 下 gap 远小于模型 | 实验 5（人类基线） |
| 为什么不消融 NL2RepoBench | 我们做了，并展示 gap 随 spec 信息量非线性增长 | 实验 4（消融） |
| Single-shot 不现实 | 也做了 agent 模式评测 | 实验 6（agent） |

---

## 实验清单

### 第一档：必须有

#### 实验 1：主结果表（Table 1）

- **行**：6-8 个模型
  - GPT-4o / GPT-5 / Claude Sonnet / Claude Opus / DeepSeek-V3 / Qwen-3 / Gemini / 开源代表
  - Human Baseline（最后一行）
  - Original Code / Oracle 上界（最后一行）
- **列**：Unit PR / Integration PR / Overall PR / Integration Gap / Normalized Score
- **工作量**：跑完 benchmark 后直接出数据

#### 实验 2：失败模式分类（Table 2 + Figure 1）

- 从所有模型的集成测试失败中随机抽 **100 个 case**
- 标注 4 类：
  - (a) 跨模块状态不一致 — Module A 写的数据 Module B 读不对
  - (b) 接口契约断裂 — A 调 B 时参数类型/含义不匹配
  - (c) 错误传播断裂 — A 抛的异常 B 没正确处理
  - (d) 单模块逻辑错误 — 和集成无关
- **Table 2**：每个类别的频率 + 每个模型的分布
- **Figure 1（堆叠柱状图）**：X 轴模型，Y 轴失败数量，颜色区分四类
- **预期**：(a)(b)(c) 合计 ≥ 70%，直接支撑 "模型不会集成" 的立意
- **工作量**：1-2 天人工标注

#### 实验 3：Case Study（正文 2-3 个）

- 每个失败类别挑一个最典型的例子
- 展示格式：
  - Spec 原文（相关段落）
  - 模型 Module A 的实现（关键代码片段）
  - 模型 Module B 的实现（关键代码片段）
  - 冲突点高亮 + 一句话解释为什么集成时挂了
- 更多 case study 放附录
- **工作量**：标注时顺手选，写入论文 0.5 天

### 第二档：强烈建议有

#### 实验 4：Spec 信息量消融（Figure 2）

- 数据源：NL2RepoBench 的 10-15 个 task
- 模型：选最强的 1-2 个
- 4 级 spec 信息量：
  - Level 4（蓝图级）：NL2RepoBench 原版 — 全部签名 + 示例 + edge case
  - Level 3（设计级）：去掉 API 示例和 edge case 测试代码
  - Level 2（行为级）：只保留行为描述 + test-interface contract（≈ E2ECodeBench）
  - Level 1（最简级）：只保留一段话的项目概述
- **Figure 2（折线图）**：X 轴 spec 级别，Y 轴 Integration Gap
- **预期**：Level 4→3 gap 小幅上升，Level 3→2 非线性跳变 — 这个转折点就是"翻译→设计"的边界
- **工作量**：改写 spec 1 天 + 跑实验 1 天 = 2-3 天

#### 实验 5：Human Baseline

- **参与者**：3-5 个 CS 本科高年级 / 研究生
- **任务**：5 个 task 的行为规格
- **限时**：每个 task 4 小时
- **收集**：Unit PR / Integration PR / Integration Gap
- **写进 Table 1**，不单独开表
- **预期**：人类 gap 远小于模型（< 10 vs 模型 30-40+）
- **工作量**：找人（今天开始）+ 等结果约 7 天 → 并行进行

#### 实验 6：Single-shot vs Agent（Table 3）

- 同一批模型，两种模式：
  - Single-shot：给 spec，模型一次性输出完整项目
  - Agent：模型可以迭代——生成 → 跑测试 → 看 output → 修复 → 重跑
- **Table 3 列**：Model / Single-shot Gap / Agent Gap / Gap 缩减率 / Agent 轮数
- **预期发现**：
  - Agent 模式 gap 缩小但仍显著 → "即使有测试反馈仍难以修复集成问题"
  - 某些失败类别可被 agent 修复（单模块逻辑错误），某些不可（跨模块状态不一致）
- **工作量**：1-2 天

### 第三档：有最好

#### 分析 A：任务复杂度 vs Gap（Figure 3）

- **散点图**：X 轴任务复杂度（模块数 / 跨模块交互数 / 总测试数），Y 轴 Integration Gap
- 看 gap 是否随复杂度超线性增长
- 如果是 → "系统集成难度随复杂度非线性增长"

#### 分析 B：跨 Benchmark 排名对比（Figure 4）

- **平行坐标图 / bump chart**
- 左轴：模型在 HumanEval / SWE-bench 的排名
- 右轴：模型在 E2ECodeBench 的排名
- 如果排名交叉 → 证明测的是一个独立能力维度

#### 分析 C：可恢复性分析

- 集成测试失败后给模型看 test output + error trace
- 单轮修复的成功率，按失败类别分
- 和实验 6 互补但粒度更细

---

## 图表总览

| 编号 | 类型 | 内容 | 位置 | 优先级 |
|------|------|------|------|--------|
| Table 1 | 表 | 主结果 + 人类基线 + oracle | 正文 | 必须 |
| Table 2 | 表 | 失败模式分类统计 | 正文 | 必须 |
| Table 3 | 表 | Single-shot vs Agent | 正文 | 强烈建议 |
| Figure 1 | 堆叠柱状图 | 各模型失败模式分布 | 正文 | 必须 |
| Figure 2 | 折线图 | Spec 信息量 vs Integration Gap | 正文 | 强烈建议 |
| Figure 3 | 散点图 | 任务复杂度 vs Gap | 正文/附录 | 可选 |
| Figure 4 | 平行坐标图 | 跨 benchmark 排名对比 | 正文/附录 | 可选 |
| Case Study | 代码对比 | 2-3 个典型集成失败 | 正文 | 必须 |

---

## 16 天排期

| 时间 | 任务 | 依赖 |
|------|------|------|
| 7/12（今天） | 找人类基线参与者（3-5 人） | 无 |
| 7/12 - 队友交付前 | 写 Introduction + Related Work + 方法论 | 无 |
| 队友交付 Day 1-3 | 跑主实验：所有模型 × 所有 task（Table 1） | 队友交付 |
| Day 3-4 | 失败模式标注 100 case + 选 case study（Table 2 + Fig 1） | 主实验完成 |
| Day 4-6 | NL2RepoBench 消融实验（Figure 2） | 主实验完成 |
| Day 5-7 | Agent 模式实验（Table 3） | 主实验完成 |
| Day 1 起并行 → ~Day 10 | 收人类基线结果 | 找到参与者 |
| Day 8-12 | 写实验部分 + 分析 + Case Study | 所有实验完成 |
| Day 12-14 | 全文打磨 + 附录 + 图表美化 | 初稿完成 |
| Day 14-16 | Buffer / 导师反馈修改 | 无 |

---

## 待确认

- [ ] 队友 benchmark 预计交付时间？
- [ ] 要跑哪些模型？（确认 API access）
- [ ] 人类基线参与者找谁？
- [ ] NL2RepoBench 的 task 选哪些做消融？
