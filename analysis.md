\## 模型测试结果分析



在完成 reference implementation 的测试后，本实验进一步选取了 Doubao-Seed-2.0、DeepSeek-V4-Pro 和 GPT-5.5 Thinking 三个模型生成的 `budgetmini.py` 程序进行评测。三个模型均使用同一份 `prd.md` 作为输入，不额外提供 `rubric.json`、reference 代码或评分器代码，以尽量保证测试结果能够反映模型根据需求文档独立实现程序的能力。



从最终结果来看，reference implementation 通过了全部 30 个测试用例，整体得分、unit score 和 system score 均为 1.0，说明当前 PRD、rubric、reference 和 evaluator 四部分是基本对齐的，评测流程本身可以正常运行。三个模型中，DeepSeek-V4-Pro 的整体表现最好，通过 20/30 个测试用例，综合得分为 0.704545；GPT-5.5 Thinking 通过 18/30 个测试用例，综合得分为 0.636364；Doubao-Seed-2.0 的原始输出代码虽然能够通过基本语法检查，但没有正确执行命令行逻辑，也没有输出有效的 state JSON，因此 30 个测试用例全部失败，最终得分为 0。



比较特殊的是，DeepSeek-V4-Pro 和 GPT-5.5 Thinking 的 system score 反而高于 unit score。DeepSeek-V4-Pro 的 unit score 为 0.5625，system score 为 0.785714；GPT-5.5 Thinking 的 unit score 为 0.5，system score 为 0.714286。这与最初预期的“unit 表现较好、system 表现较差”并不完全一致。进一步查看失败用例后可以发现，造成这种结果的主要原因并不是系统级测试过于简单，而是两个模型都在 category 处理逻辑上采取了更严格的解释。具体来说，它们都要求 `Food`、`Income` 等 category 必须提前显式创建，之后才能添加对应 category 的 transaction；而在本任务的 rubric 中，部分交易测试允许在添加交易时直接使用 category 名称。因此，很多和添加交易相关的 unit case 直接失败，后续的编辑交易、删除交易、报告统计、payee/tag 记录等功能也受到连锁影响。



这一现象说明，模型并不一定是在所有功能上都失败，而是可能因为对某个需求细节理解不一致，导致一批相关测试同时失效。DeepSeek-V4-Pro 和 GPT-5.5 Thinking 都能够完成账户、预算、部分系统联动等功能，但在“交易是否允许直接绑定未预创建类别”这一点上没有和 reference 行为保持一致。因此，本次实验体现出的主要问题不是单纯的代码能力不足，而是需求文档中的隐含约定被模型理解成了更严格的业务规则。



从 E2E-Bench 的角度看，这个结果仍然具有分析价值。一方面，Doubao-Seed-2.0 的结果表明，模型生成的代码即使看起来完整，也可能没有形成真正可执行的 CLI 程序；另一方面，DeepSeek-V4-Pro 和 GPT-5.5 Thinking 的结果说明，模型在局部功能实现上已经具备一定能力，但对于跨功能链路中的状态更新、前置条件假设和需求解释仍然比较敏感。尤其是当一个基础对象的处理逻辑出现偏差时，后续 transaction、report、budget、rule 等多个模块都会受到影响，这正是端到端评测相比单点功能测试更容易暴露的问题。



