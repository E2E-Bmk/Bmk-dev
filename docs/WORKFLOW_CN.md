# SWE-E2E Benchmark 构建流水线 — 全流程中文说明

> 本文档基于 `Bmk-dev/skills/` 目录下各阶段 SKILL.md 和 `PIPELINE_STATE.template.md` 整理。
> 适合在新任务启动前、阶段交接前或出现异常时参考。

---

## 一、整体架构

### 目标

从真实 Python 开源仓库中，构造**可复现、公平、行为性**的软件工程重建评测任务。候选 agent 只能看到公开行为规格说明书（spec），在不接触原始源码、测试、评分结果的条件下独立实现，用 oracle 测试集评分。

### 流水线结构

```
candidate-selector → spec-writer → test-filter → [evaluation] → task-judge
       ↑                 ↑              ↑                              |
       └── retire ───────┴── spec gap ──┴── filter issue ─────────────┘
```

| 阶段 | Skill | 主要产出 |
|------|-------|---------|
| Stage 1：候选筛选 | `candidate-selector` | `filter_notes.md`、CANDIDATES.md 条目 |
| Stage 2：规格撰写 | `spec-writer` | `spec_vN.md`（通过11项验证） |
| Stage 3：测试过滤 | `test-filter` | `spec_test_map.md`、`kept_nodeids.txt`、`taxonomy.jsonl` |
| Stage 4：候选评估 | _（仅运行候选 agent）_ | agent 轨迹、`score_result.json` |
| Stage 5：裁判诊断 | `task-judge` | `diagnosis_report.md`、weakness table 条目 |

### Workspace 目录结构

```
Bmk-dev/
├── wip/{task-id}/               ← 进行中的构建工作
│   ├── PIPELINE_STATE.md        ← 任务状态机实例
│   ├── filter_notes.md          ← Stage 1 输出
│   ├── spec/
│   │   ├── spec_vN.md
│   │   └── spec_patch_request.md
│   ├── filter/
│   │   ├── rewrite_audit.md
│   │   ├── candidate_filter_map.md
│   │   ├── rewritten_upstream_tests.py
│   │   ├── kept_upstream.txt
│   │   ├── generated_tests.py
│   │   ├── spec_test_map.md
│   │   ├── kept_nodeids.txt
│   │   ├── taxonomy.jsonl
│   │   ├── coverage.json
│   │   ├── coverage_gaps.txt
│   │   └── reference_score.json
│   └── judge/
│       └── diagnosis_report.md
├── tasks/{task-id}/             ← QUALIFIED 任务（从 wip/ 毕业）
├── candidate-runs/              ← 评估运行记录
├── skills/                      ← 各阶段 SKILL.md（运行时权威）
├── CANDIDATES.md                ← 候选选入与退休日志
└── weakness_table.md            ← 跨任务模型弱点记录
```

---

## 二、核心三原则（贯穿全流程）

这三条原则是 task-synthesizer 审查**所有子 agent 输出**的判断标准。每个阶段的输出在推进前都必须对照这三条原则审查。

### 原则 1：Like a developer（像库作者）

Spec body 必须读起来像库作者写给用户的 API 文档，而**不是** benchmark 产物。任何一个句子读起来像是写给评估系统的（含 task ID、audit 语言、evaluation apparatus），都必须改写。

### 原则 2：Spec-driven（规格驱动）

每一条保留的测试必须可追溯到 spec 中的某个具体节。每一个裁判判决必须引用 spec 覆盖情况。测试无法映射到 spec → verifier 问题；失败无法用 spec 缺口解释 → verifier 问题，不是模型问题。

### 原则 3：Behavioral（行为性）

测试检查任何正确重现实现都会产生的**可观察输出**。失败必须反映真实的能力缺口，而非协议产物（精确字符串、内部名称、fixture shape）。如果失败集中在未文档化的内部结构上 → 测试工具有问题。

---

## 三、状态机机制

### PIPELINE_STATE.md 结构

每个任务在 `wip/{task}/PIPELINE_STATE.md` 维护一个运行中的状态机实例。

```
state:       S1_SCREENING        ← 当前状态
stage:       1
spec_iter:   0                   ← spec 循环计数（> 3 → 上报）
filter_iter: 0                   ← filter 循环计数（> 2 → 上报）
eval_iter:   0                   ← eval 循环计数（> 2 → 上报）
updated:     {DATE}
```

### 操作规则

- **新任务：** 从 `wip/_template/PIPELINE_STATE.md` 复制，替换 `{TASK_ID}` 和 `{DATE}`
- **分派子 agent 前：** 读 `PIPELINE_STATE.md`，确认 `state` 与即将运行的阶段匹配。不匹配 → 先解决状态不一致，不分派
- **子 agent 返回后：** 检查 `PIPELINE_STATE.md` 是否已更新（state 已转移，History 已追加）。未更新 → 视为失败，重新运行
- **循环终止：** `spec_iter > 2`、`filter_iter > 2` 或 `eval_iter > 2` 且未解决 → 设 `state → RETIRED`，不再继续

### 禁止转移（任何状态下均适用）

| 目标状态 | 前置要求 | 违反后行动 |
|---------|---------|----------|
| `S3B_TRIGGER` | `filter/rewrite_audit.md` 必须存在 | 回 `S3A_REWRITE` |
| `S3_ORACLE_MERGE` | `kept_upstream.txt` 或 `generated_tests.py` 至少一个存在 | — |
| `S4_SETUP` | `filter/reference_score.json` 存在且 pass rate = 100% | — |
| `S5_JUDGE` | `candidate-runs/.../score_result.json` 存在 | — |

---

## 四、Stage 1：候选筛选（candidate-selector）

### 状态机接口

- **入口状态：** `S1_SCREENING`
- **通过出口：** → `S1_SELECTED`，追加 History 行
- **拒绝出口：** → `RETIRED`，追加 History 行，停止

### 硬性拒绝条件（任意一条触发即 reject）

| 条件 | 说明 |
|------|------|
| 源码 < 3000 行 | 规模过小，无重建价值 |
| 可用单文件实现 | 结构过于简单 |
| 无跨 ≥2 个公开投影的共享状态 | 缺乏多视图不变量（如 CLI + API + 文件状态） |
| 测试套件缺失 / 网络依赖 / >70% 快照测试 | 无法构成公平 oracle |
| 核心行为是高饱和标准模式 | 模型可凭训练记忆实现（如 Jinja2、Redis、argparse） |
| 评分需要私有实现细节 | 无法构建公平评分工具 |
| Docs-test 投影不匹配 | 公开文档仅覆盖 CLI/语法，测试套件测试 Python API 内部 |

### 软性偏好（正向信号）

- 有持久状态：文件树、数据库、事件日志、模板、索引、缓存
- 多公开投影面向同一事实：CLI、Python API、文件输出、搜索、schema 自省
- 官方文档有足够行为覆盖，可写出可追溯的 spec
- 无强制外部服务；网络调用可移除或可 mock
- 测试文件顶层仅导入公开 API 符号（无 `from pkg._xxx import`）

### 测试 Import 预筛（必须在写 filter_notes.md 之前执行）

```bash
grep -rn "from <pkg>\._\|import <pkg>\._" tests/
```

- > 30% 测试文件有模块级私有导入 → 标注 `test_import_audit: HIGH_RISK`
- 不阻止选入，但必须标注——Stage 3 Track A 将需要大量改写或提前触发 Track B

### 产出物：filter_notes.md（所有字段必填）

```
repo:               {name}
source_path:        {local or URL}
commit:             {hash}
src_loc:            {N}
test_functions:     {N}
test_files:         {list or count}
dominant_test_styles: {unit/integration/snapshot/...}
public_docs:        {使用的文档页面列表}
core_fact_source:   {共享状态是什么}
derived_views:      {公开投影列表}
external_deps:      {依赖列表及隔离方案}
test_import_audit:  {clean | HIGH_RISK — 估计受影响测试文件比例}
docs_test_alignment:{aligned | MISMATCH}
contamination_note: {repo}@{version}, released {date}, cutoff relation: {before|after|unknown}
decision:           {keep | defer | reject}
reason:             {一句话理由}
risks:              {主要风险}
```

通过后追加 `CANDIDATES.md`：

```markdown
| {repo} | SELECTED | {src_loc} | {test_count} | {reason} |
```

---

## 五、Stage 2：规格撰写（spec-writer）

### 状态机接口

- **入口状态：** `S2_SPEC_DRAFT` 或 `S2_SPEC_CHECK`
- **`spec_iter > 3` → 停止，上报 orchestrator，不得继续**
- **全部通过出口：** `S2_SPEC_DONE` → `S3A_IMPORT_AUDIT`，追加 History
- **失败出口（循环）：** → `S2_SPEC_DRAFT`，`spec_iter += 1`

### 两个核心过滤问题

每一个纳入 spec 的内容项，必须同时回答：

**Q1 — 属于公开行为契约吗？**
> 库通过其预期的外部接口承诺给调用者的内容。
> - 是 → 继续 Q2
> - 否 → 省略

**Q2 — 是不可推导的吗？**
> 高级工程师能否从领域知识、设计判断或通用实践中推断出来，而无需阅读库的源码或文档？
> - 是，可推导 → 省略（模型自己能搞定）
> - 否，库特有 → 明确写入

### 读源码流程（写 spec 之前必须完成）

1. 读 `__init__.py` 和 `__all__`，产出**公开 API surface 列表**：每个导出名称 + 文件路径。列表为空 → 停止，说明没读到位
2. 读文档正文（不只是标题）：扫描 `from pkg.module import Name` 模式、返回值示例中的 NamedTuple 类名、用户需要 catch 或比较的异常类
3. 对 surface 列表上的每一项**逐一**回答 Q1 → Q2，禁止批量决策
4. 完整处理 surface 列表后，再开始写 spec 节

### 必须包含的内容

仅当通过 Q2（高级工程师无法从通用知识推导）时才写入：

- 所有公开导入路径和名称：函数、类、异常、namedtuple，包括 re-export 的别名
- 函数签名：参数名、类型、默认值——仅当默认值或参数名是库特有且非显然的
- 文档化的命名空间、引擎和数据模型
- 特殊用户可见的 context key
- 错误语义：哪个触发条件 → 哪个异常类（当异常类型是库特有或非显然时）
- **Product State Model**：在各子系统节之前，写一个顶层状态模型，列举库核心状态的至少3个公开投影，并写出至少3条跨视图不变量
- **Cross-View Invariants**：≥6 条，用户可观察语言，覆盖所有公开投影对。每条用 `must` 或 `returns`，绝不用 `can` 或 `may`
- 每条行为语句用 `must when [条件]` 而非 `can`；条件必须明确
- 每条行为描述含 failure path：违反前置条件时 `must raise` 或 `must return` 什么
- ≥1 个完整端到端工作流示例
- Evaluation Notes：测试维度说明，不含 fixture shape

### 绝不包含的内容

- 内部模块/文件组织（工程师自行决定）
- 算法步骤序列（"Step 1: load JSON, Step 2: iterate keys"）
- 框架选择（"用 Click 做 CLI"）
- 依赖版本约束
- 未出现在公开导出 surface 的内部辅助名（在测试 import 中出现不算充分，需核查 `__all__`、`__init__` 和用户文档）
- 私有名称（`_name`、`__name`）
- 公开类的内部实现细节（字段名、内部 map、单例结构）

### Spec 文件结构

**Internal header**（发给候选前必须剥离）：

```
<!-- INTERNAL
task_id: {task-id}
spec_version: v{N}
delta: {与上一版本相比新增/删除的内容及原因}
source_boundary: {查阅的文档页面、源文件列表}
-->
```

**Candidate-visible body**（读起来像库作者文档）：

```
# {Library} Specification

## Product Overview
## Scope                       ← 覆盖哪些功能域的正向列表
## Installable Surface         ← 导入路径、CLI 入口点
## Public API                  ← 签名、参数语义、数据对象
## Behavioral Sections         ← 各领域状态/操作契约
## Error Semantics             ← 异常类 → 触发条件
## Cross-View Invariants       ← ≥6 条，用户可观察语言
## Representative Workflow(s)  ← ≥1 个端到端示例
## Non-Goals                   ← 明确排除项
## Evaluation Notes            ← 测试维度说明，无 fixture shape
```

### 11 项验证清单（全部通过方可推进）

| # | 检查项 |
|---|--------|
| 1 | 每个 feature 可追溯到公开文档的"新手必知"，而非"有经验工程师的设计选择" |
| 2 | 无内部类名或未导出的 module path |
| 3 | 不变量用行为语言描述（非代码） |
| 4 | Non-goals 明确列出 |
| 5 | 无任何节隐含隐藏的 fixture shape |
| 6 | 所有行为语句用 must / returns / raises，不用 can / may |
| 7 | 所有条件行为已显式写出条件（must when [X]，非"when applicable"） |
| 8 | 每个行为描述含 failure path（违反前置条件时 must raise / must return 什么） |
| 9 | 有 Product State Model 节（或等价结构），含 ≥3 条跨视图不变量 |
| 10 | 无 escape hatch（措辞模糊到候选可跳过某行为而仍满足 spec 表述） |
| 11 | 所有优先级/覆盖规则/多源合并经 reference 实际执行验证，而非仅从文档推断 |

任意一条失败 → 修补后重新验证全部 11 条。

### Spec 补丁（处理来自 task-judge 的 spec_patch_request.md）

`spec_patch_request.md` 携带 `type` 字段，处理方式不同：

**type: spec_gap** — reference 中存在但 spec 遗漏的行为。用标准文档推断添加缺失行为。

**type: spec_error** — spec 当前声称 X，但 judge 观察到 reference 实际行为是 Y。处理步骤：
1. 用请求中提供的**精确冲突输入**重新执行 reference，直接观察输出
2. 确认 judge 的观察值与 reference 实际输出一致
3. 确认后：将 spec 声明修正为 reference 观察值；若与其他 spec 语句矛盾，一并解决
4. 若 reference 产生第三个值 Z：修正为 Z，并注明 judge 证据不完整

**绝不仅凭文档推断修正 spec_error，必须以 reference 执行为依据。**

补丁写入原则：
1. **附加到最近的宿主，不创建新结构**——缺口是参数/CLI 选项/边界条件时，加到最近的现有代码块或行为列表
2. **仅对独立概念域创建新节**——有独立初始化/使用/销毁生命周期且无法自然融入现有节时
3. **写行为语言，而非补丁语言**——避免"also supports"、"additionally"；直接陈述行为，仿佛它一直存在

---

## 六、Stage 3：测试过滤（test-filter）

### 状态机接口

- **入口状态：** S3 系列任一状态。不确认 state 不开始工作
- **`filter_iter > 2` → 停止，上报 orchestrator**
- **禁止转移硬性检查：** `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在；不存在则先回 `S3A_REWRITE`

### 两个核心过滤标准

每个保留决定都归结为这两个问题，**两个都必须为"是"才保留**：

**Q1 — Behavioral（行为性）？**
> 使用不同内部结构的正确重现实现，也能通过这个测试吗？
>
> 检查精确字段名、repr 字符串、内部 map、异常消息措辞或单例 shape 的测试 → 回答否 → **排除**

**Q2 — Spec-derivable（可从 spec 推导）？**
> 只读过 spec 的高级工程师能推断出这个测试的预期结果吗？
>
> 无法映射到 spec 中某个具体点的测试 → 回答否 → **排除**

### 机械预过滤（任意一条匹配 → 立即排除，无需进一步判断）

逐 nodeid 扫描，非逐文件：

1. **私有 import** — 导入私有符号：`from lib._xxx import ...` 或 `import lib._xxx`
2. **私有断言** — 断言私有属性或访问 `obj._field` / `obj.__dict__`
3. **环境依赖** — 发出网络请求、使用绝对文件系统路径、读取测试本身未注入的环境变量
4. **fixture 副作用依赖** — setup 要求调用公开功能 A 仅为构造功能 B 的输入，而 A 并非被测行为

---

### Track A：上游测试清理

#### Step 1：Import 审计与公开 API 改写（文件级）

对每个测试文件扫描顶层 import，分类处理：

| Import 类型 | 示例 | 处理方式 |
|---|---|---|
| 独立测试辅助文件 | `from tests.util import assert_ppo` | 将 `tests/util.py` 复制到 harness 环境；保留文件 |
| 包内纯常量 | `from pkg import _URL_RE` | 通过 conftest.py 注入常量；保留文件 |
| 上游测试基础设施 | `from pkg.tests.base import BaseTestCase` | 尝试改写：用等价的公开 API 调用替换；可改写则保留，否则丢弃 |
| 库内部（单向） | `from pkg._parser import _P`（`_P` 不构造候选必须实现的类型） | 从 reference 预填；保留文件 |
| 库内部（双向） | `from pkg._parser import _P`（`_P` 构造候选必须实现的类型） | 尝试用公开 API setup 替换；可改写则保留，否则丢弃 |
| In-process runner | `from pkg.main import run` | 尝试用公开 CLI/API 入口点改写；runner 本身是被测行为则丢弃 |
| 范围外模块 | `from pkg.other import X`（X 不在 spec 范围内） | 丢弃整个文件 |

**共享 fixture/辅助文件清理（必须在逐节点工作前完成）：**
先扫描所有共享 fixture 文件（`tests/conftest.py`、`tests/helpers.py`、`tests/util.py`、被多个测试文件导入的任何文件），移除或替换每个私有 import。辅助函数无法用公开 API 表达则移除该函数，并将调用它的所有测试标记为 `excluded`。**此步骤必须在逐函数工作之前完成。**

**逐函数原子提取（单元测试文件）：**
当单元测试文件有无法在文件级移除的私有模块级 import 时，**不丢弃整个文件**，而是逐一扫描**每个**测试函数（非抽样）：
1. 函数体引用了私有符号？→ 在 `candidate_filter_map.md` 中标记 `excluded`，注明具体私有符号
2. 函数体只使用 spec 中的公开 API 名？→ 提取到 `filter/rewritten_upstream_tests.py`，修正 import（仅公开路径），分类为 `atomic` 层

**改写有效性标准：**
- 改写后的测试检验相同的行为契约
- setup 只使用 spec 中列出的公开 API 名
- 测试在错误实现上仍会失败

改写审计记录在 `rewrite_audit.md`；实际改写代码必须出现在 `filter/rewritten_upstream_tests.py`。仅有审计记录、没有对应函数代码 = 尚未完成改写。

**Step 1 完成前必须更新状态：** 统计所有保留文件中测试函数总数，写入 `PIPELINE_STATE.md` 的 `functions_in_scope`。此值设定后只读，后续步骤不得修改。

**Track B 提前触发：** 改写尝试后 >50% 的测试文件被丢弃 → 立即并行启动 Track B。

#### Step 2：公平性审计（nodeid 级）

逐 nodeid 对比断言面与公开文档：

**排除（断言检查以下内容）：**
- 文档未指定的精确 repr() 输出
- 文档中缺失的内部对象字段或 dataclass 槽
- 私有属性名（即使无下划线前缀也可访问）
- 精确异常消息文本（异常类型可接受；消息措辞不可接受）
- 解析器内部 map、单例注册表或实现 shape 不变量
- `isinstance(x, InternalClass)`（内部类未文档化为公开 API 的一部分）

**保留（断言检查以下内容）：**
- 公开 API 参考文档中的返回值语义
- 文档化公开工作流产生的文件/数据库/stdout 副作用
- 文档化错误条件中的异常类型
- API 参考或示例中文档化的公开属性值

#### Step 3：Dummy Gate

对整个保留集运行 dummy 实现（所有公开函数 `return None` / `raise NotImplementedError`）。丢弃通过 dummy 的测试——这些测试在结构上是微不足道的，不是难度证据。

**产出物：** `filter/kept_upstream.txt`

**Step 3 完成前必须更新状态：**
- 统计 `filter/rewritten_upstream_tests.py` 中的函数数量 → 写入 `functions_kept`
- 统计 `candidate_filter_map.md` 中的 `excluded` 行数 → 写入 `functions_excluded`
- 验证 `functions_kept + functions_excluded = functions_in_scope`；不等 → 回 Step 2 处理缺失函数

**Track A 终止：** 保留 nodeid < 30，或所有文件均被丢弃 → 进入 Track B。

---

### Track B：覆盖引导生成

#### 触发条件

**提前触发（立即并行启动，不等 Track A 完成）：**
- Step 1 改写尝试后 >50% 测试文件被丢弃（import 饱和）
- 所有上游文件在 Step 1 全部被丢弃

**延迟触发（Track A 完成后评估）：**
- Track A 最终保留数 < 30 nodeids
- Track A 保留数 ≥ 30，但保留集大多是 atomic 或 implementation-shaped，缺乏 integration/system_e2e 覆盖

#### Step 1：对 reference 运行 branch coverage

```bash
# 隔离 venv，安装 reference 包（非候选）
coverage run --branch --source=<pkg> -m pytest filter/kept_upstream.py
coverage json -o filter/coverage.json
```

若 Track A 产出零测试，用最小 smoke import：

```bash
coverage run --branch --source=<pkg> -c "import <pkg>"
```

#### Step 2：格式化缺口供生成 agent 使用

```bash
python tools/format_coverage.py filter/coverage.json <source_root>
```

产出 `filter/coverage_gaps.txt`，含未覆盖分支及周边源代码行注释。

#### Step 3：生成 agent（Codex subagent / Claude Code）

给 agent 提供：
- `filter/coverage_gaps.txt`
- `spec/spec_vN.md`
- 对 reference 实现的**执行权限**（可 import 和运行；**不得**读取源文件）

**任务：** 通过调用 reference 的变化输入来覆盖缺失分支，观察实际输出，然后从观察结果构造断言。

**每节最低覆盖配额（调用 agent 前必须枚举所有 H2/H3 节，计算当前覆盖数）：**

| 节类型 | 最低测试数 |
|--------|----------|
| `Cross-View Invariants` | ≥ 5 |
| `Error Semantics` | ≥ 3 |
| Main workflow / Representative Workflows | ≥ 3 |
| 其他所有节 | ≥ 3 |

**全局底线：** Track A + Track B 合并 oracle 必须包含至少 **50 条可评分测试**方可推进 Stage 4。

生成协议（必须写入 agent prompt）：
1. 调用 `reference_pkg.fn(input)` 并记录真实返回值/副作用
2. 从观察结果写测试断言，不从 spec 推断
3. 每个生成的测试验证：这个 I/O 关系可从 spec 推导吗？不能 → 丢弃，**不补充 spec 内容**
4. 生成完毕后验证每个强制目标节达到最低数量，且总 oracle ≥ 50

禁止事项（在 prompt 中明确约束）：
- 不得读取 reference 源文件，只能执行
- 断言只针对观察到的返回值和副作用
- 无 repr、无内部状态、无精确错误消息文本
- 每个测试必须断言在错误实现上会失败的内容

#### Step 4：Dummy Gate（同 Track A Step 3）

对生成测试运行 dummy stubs，丢弃通过的。

#### Step 5：Reference Gate

对生成测试运行 reference 实现，要求 **≥ 95% 通过**。低于则将失败测试返回 agent 修正，`filter_iter += 1`。

**产出物：** `filter/generated_tests.py`

---

### Oracle 合并

```
oracle = kept_upstream.txt 中的测试  +  generated_tests.py 中的测试函数
```

写 `filter/spec_test_map.md`，列出所有 oracle 测试：

```markdown
| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| tests/test_foo.py::test_bar | atomic | Public API - foo() | covered | |
| tests/test_baz.py::test_workflow | system_e2e | Workflow + State Invariants | covered | source: generated |
```

**Status 值说明：**

| Status | 含义 | 处理 |
|--------|------|------|
| `covered` | 在 spec 中，或高级工程师可从 spec 推导 | 保留 |
| `spec_gap` | 行为有公开文档依据但 spec 遗漏 | 补丁 spec → 重标为 covered |
| `source-only` | 行为是任意实现选择，公开文档无规定 | 排除 |
| `excluded` | 机械预过滤规则匹配 | 排除 |

文件底部必须包含：

```
Total: N | kept (covered): N | spec_gap: N | source-only: N | excluded: N | final scoreable: N
```

若 oracle 全为 Track B 生成（无上游测试幸存），在 `spec_test_map.md` 头部标注 `oracle_source: generated_only`——task-judge 将执行额外抽检。

**离开 oracle merge 前必须更新状态：**
- 统计 `spec_test_map.md` 所有 `covered` 行 → 写入 `oracle_count`
- `oracle_count < 50` → **不推进 S4_SETUP**，返回 Track B 生成扩充覆盖

### 评分器隔离要求

所有对 `kept_nodeids.txt` 的评估运行必须使用 `--remove-path <pkg>`（或等价隔离标志），防止系统安装包遮蔽候选方案。在任务 `MANIFEST.json` 的 `scorer_isolation` 字段记录隔离方法。**未使用此标志产出的分数无效，必须丢弃。**

### taxonomy.jsonl 格式

```jsonl
{"taxonomy_key": "test_foo::test_bar", "layer": "atomic"}
{"taxonomy_key": "test_baz::test_workflow", "layer": "system_e2e"}
```

Key 生成算法：去除参数后缀（如 `[case0]`），用文件 stem 替换文件路径，类名和方法名用 `.` 连接。例：`tests/test_req.py::TestParsing::test_valid` → `test_req.TestParsing.test_valid`。

---

## 七、Stage 4：候选评估（evaluation）

### 状态机接口

- **入口状态：** `S4_SETUP`（前置：`filter/reference_score.json` 存在且 pass rate = 100%）
- **评估环境：必须在 Linux 或 WSL 中运行，不得在 native Windows 执行**

### 候选 Packet 组装规则

候选 agent 只能看到：
- Spec body（**剥离 `<!-- INTERNAL ... -->` 头部后**的内容）

候选 **不得** 看到：
- 源代码仓库
- 测试文件或 fixture 文件
- Score 报告或历轮尝试输出
- `spec_test_map.md` 或 `kept_nodeids.txt`
- Workflow skills 或任何内部产物

### 评估流程

```
S4_SETUP → S4_EVAL_RUN → S4_ANALYSIS → S4_DONE
```

**S4_SETUP：**
- 准备 cleanroom 候选评估环境
- 组装 candidate packet（仅 spec body）

**S4_EVAL_RUN：**
- 运行候选 agent
- 产出：`candidate-runs/{run}/score_result.json`
- 运行命名格式：`{model}-{task}-{spec}-{date}-{run}/`

**S4_ANALYSIS：**
- 检查分数分布，排查饱和/异常
- 分数饱和（候选 pass rate = 100% 且实现文件数远少于原包）→ 循环回 `S2_SPEC_DRAFT`（`spec_iter += 1`）
- Oracle 质量问题 → 循环回 `S3_ORACLE_MERGE`（`filter_iter += 1`）

评估完成后**始终推进到 task-judge**，即使运行被中断或检测到环境异常（在诊断报告中注明，必要时重跑）。

---

## 八、Stage 5：裁判与诊断（task-judge）

### 状态机接口

- **入口状态：** `S5_JUDGE`（前置：`candidate-runs/.../score_result.json` 存在）
- **QUALIFIED 出口：** `state → QUALIFIED`，执行 terminal todo
- **循环 spec gap：** `state → S2_SPEC_DRAFT`，`spec_iter += 1`；> 3 → `RETIRED`
- **循环 filter issue：** `state → S3_ORACLE_MERGE`，`filter_iter += 1`；> 2 → `RETIRED`
- **循环 cheat/env：** `state → S4_SETUP`，`eval_iter += 1`；> 2 → `RETIRED`

### 核心原则：先验证工具再读分数

> **评分集中的每一个测试必须是 spec-driven 且 behavioral 的。在读任何分数之前先应用这一原则。**

- **Spec-driven**：测试可追溯到某个 spec 节；预期结果仅从 spec 可推导
- **Behavioral**：任何正确重现实现都会产生的可观察行为——非内部字段名、repr 字符串、异常消息措辞或实现特有 shape

不满足任意一条的测试上的失败是 **verifier failure**，不是 model failure。

### 3 项硬性检查（全部通过才能认为结果有效）

#### 检查 1：Anti-Cheat（防作弊）

**读任何分数之前**，执行 import provenance preflight：

```bash
python -c "import <pkg>; print(<pkg>.__file__)"
```

**必须将此命令的字面输出写入诊断报告的 `Preflight output` 块，然后才能打开任何分数文件或引用任何分数值。此块缺失 → 报告在结构上无效，不得推进。**

输出必须指向候选方案目录，而非 oracle worktree 或任何已安装包。确认后，扫描 agent 的完整轨迹/日志，检查任何不应访问的信息。

**禁止访问模式（任何匹配 → 标记 `CHEAT_DETECTED`，丢弃分数）：**
- 读取源码仓库路径下的任何文件（`repo-pool/`、oracle worktrees、reference 环境）
- `pip install <target-library>` 或任何拉取目标包的安装
- 读取含预期值的测试文件或 fixture 文件
- 读取 score 报告、历轮尝试输出或任何评估产物
- 从非候选路径导入目标库（由 preflight 确认）
- 在实现阶段读取 `spec_test_map.md` 或 `kept_nodeids.txt`

高分运行中发现上述任意一条 → 无效，不论分数多高。

#### 检查 2：Solvability（可解性）

在**库特定依赖环境**（非通用共享环境）中运行 reference 实现对评分集进行测试。

- 若 reference pass rate 显著低于评分集大小：先诊断（缺失依赖、pytest 插件、环境配置错误）→ 修复环境 → 重跑
- 修复后仍低 → 评分集有损坏测试 → 返回 test-filter 修复
- **reference pass rate < 95% 的任务不得标记 QUALIFIED**

#### 检查 3：Fairness（公平性）

**Gate A — Spec 映射抽查**

从 `spec_test_map.md` 的 `covered` 行中抽样。对每个抽样测试，验证 spec_section 映射正确——只读该 spec 节的高级工程师能预测测试结果吗？映射错误 → 返回 test-filter 修正。

**Gate B — 失败模式审计**

评分后，抽样失败测试，检查是否符合两条原则：
- 失败可追溯到文档化的 spec 行为吗？否 → 测试在检查未文档化的内部 shape → verifier failure
- 失败代表可观察的行为缺口，还是内部结构不匹配？

多数失败集中在未文档化的 atomic 内部 shape → BROKEN/fairness，返回 `filter_correction_request.md` 到 test-filter。

**Gate C — Generated-only Oracle 抽检**

若 `spec_test_map.md` 头部含 `oracle_source: generated_only`，人工抽样 ≥5 个生成测试，对每个重新应用两条原则：
- **Spec-driven**：断言的预期值可从具体 spec 节推导吗？还是生成器从自己的 spec 阅读推断（循环论证）？
- **Behavioral**：不同内部结构的正确实现也会通过吗？还是在检查 repr 格式、内部字段名或精确错误消息文本？

Gate C 失败 → 返回 `filter_correction_request.md` 到 test-filter 重新生成。

**Gate D — 覆盖缺口审计**

对 spec 中每个 H2/H3 节，检查 `spec_test_map.md` 是否有至少一条 `covered` 行映射到该节：

| spec 节 | 未覆盖行为 | 影响 | 建议 |
|---------|-----------|------|------|
| （示例）Cross-View Invariants | invariant #3、#5 | 高 | 生成针对性测试 |

**覆盖裁决：**
- **FULL** — 0 个 spec 节零覆盖
- **PARTIAL**（可接受）— 1-2 个次要节未覆盖；无核心不变量节为空
- **GAP**（需行动）— 任何核心不变量节（`Cross-View Invariants`、`Error Semantics`、状态生命周期节）零覆盖

GAP → 发出 `filter_correction_request.md`，路由回 test-filter，生成 GAP 节的额外测试。**不得在未解决 GAP 的情况下发出 QUALIFIED。** 只有在 test-filter 已尝试生成但确认无法在不引入循环断言的情况下产出更多 spec-derivable 测试时，GAP 才可作为 caveat 接受（须在 MANIFEST.json 的 `coverage-gap` 字段记录，并在诊断报告中明确说明）。

### 诊断两遍流程

#### Pass 1：验证测试工具有效性

对每个失败，先验证测试本身是否合格：

| 问题 | 答案 | 行动 |
|------|------|------|
| 失败测试可追溯到 spec 节吗？ | 否 | Verifier failure → 返回 test-filter，标记 excluded |
| 不同内部结构的正确实现也会通过吗？ | 否 | Verifier failure，测试检查内部结构 → 返回 test-filter |
| 两个都是 | — | 进入 Pass 2 |

大量失败 Pass 1 → 任务状态 `BROKEN`（fairness），发出 `filter_correction_request.md`。

#### Pass 2：模型失败分析

对通过 Pass 1 的每个失败，依次回答：

**Q-A：候选输出符合 spec 所说的应该发生的吗？**
- 是 → 模型正确实现了 spec，继续 Q-B
- 否 → 模型偏离 spec → **真实 model failure**（记录到 Step 3）

**Q-B（仅在 Q-A = 是时）：reference 实现通过这个测试吗？**
- 否 → 测试的预期值连 reference 都过不了 → verifier failure → 返回 test-filter，标记 `excluded`
- 是 → reference 通过但符合 spec 的候选失败 → **spec 有事实错误** → 发出 `spec_patch_request.md`（`type: spec_error`），路由到 spec-writer

**Legacy 分支（Q-A 无法回答——spec 沉默或模糊）：**
- Spec 模糊或不完整 → spec gap → `spec_patch_request.md`（`type: spec_gap`）
- 测试中有任意格式/内部名称 → 在 `spec_test_map.md` 标记 `excluded`

### 能力维度（用于 weakness table 分类）

| 维度 | 覆盖内容 |
|------|---------|
| `api-surface` | 缺失或错误的公开导入路径、函数名、类名 |
| `atomic-behavior` | 单函数正确性：错误输出、错误默认值、错误类型 |
| `error-semantics` | 错误异常类型、错误触发条件、缺失 raise |
| `state-management` | 错误生命周期、变更未持久化、陈旧状态 |
| `cross-view-consistency` | 同一事实的两个公开投影不一致 |
| `workflow-completeness` | 端到端工作流失败；部分实现 |

区分根因失败与级联失败：一个损坏的 import 或缺失类可级联出数十个测试失败。只统计根因失败，不统计级联失败。

### 饱和启发式（candidate pass rate = 100% 时必须检查）

若候选将上游包合并为显著更少的文件（如 4 个 vs 20+）且达到 100% pass rate：
- 应用 `trivially-solved` 和 `saturated-candidate-score` 两个标签
- 在诊断报告中记录该运行模式与从训练数据召回（而非从 spec 重建）一致
- 不阻止 QUALIFIED，但必须出现在 MANIFEST caveats 中

### 产出物

**任务状态（三选一）：**
- `QUALIFIED` — 所有硬性检查通过，评分集有效
- `BROKEN` — 可解性或公平性检查失败；任务需修复
- `CHEAT_DETECTED` — 轨迹中发现禁止访问；运行无效

**诊断报告（`judge/diagnosis_report.md`）：**
1. Anti-cheat 扫描结果（含 `Preflight output` 块）
2. Reference pass rate 及环境说明
3. 候选按层分数（atomic / integration / system_e2e）
4. 发现的协议问题及已采取的行动
5. 真实失败集群，含根因和能力维度
6. 级联分析：多少个失败根植于多少个根因

**Weakness Table（`Bmk-dev/weakness_table.md`，追加不覆盖）：**

```markdown
| model | task | dimension | description | affected_tests |
|-------|------|-----------|-------------|----------------|
| claude-sonnet | mylib | error-semantics | 对缺失 context key 抛出 ValueError 而非 UndefinedVariableError | 3 atomic |
```

---

## 九、反馈循环与终止条件

### 反馈产物

当 task-judge 发现问题时，产出以下之一：

**`spec_patch_request.md`** — spec 缺口或 spec 错误，附证据；交给 spec-writer。  
每项必须含 `type` 字段：
- `type: spec_gap` — reference 中存在但 spec 遗漏的行为；spec-writer 添加
- `type: spec_error` — spec 声称 X，reference 实际是 Y；spec-writer 必须以 reference 执行为依据修正

**`filter_correction_request.md`** — 错误分类或错误保留的测试列表；交给 test-filter

接收方处理请求后更新自己的产出物，向 orchestrator 发信号，orchestrator 随后重跑所有下游阶段。

### 循环计数规则

| 计数器 | 递增时机 | 上限 | 超限行为 |
|--------|---------|------|---------|
| `spec_iter` | 每次从任意阶段循环回 S2_SPEC_DRAFT | 3 | 直接 RETIRED |
| `filter_iter` | 每次从任意阶段循环回 S3_ORACLE_MERGE | 2 | 直接 RETIRED |
| `eval_iter` | 每次从任意阶段循环回 S4_SETUP | 2 | 直接 RETIRED |

### 各反馈路径汇总

| task-judge 裁决 | 路由 | 递增计数器 |
|----------------|------|----------|
| CHEAT_DETECTED | 修复评估环境 → S4_SETUP | eval_iter |
| BROKEN（可解性） | 修复环境或返回 test-filter → S4_SETUP | eval_iter |
| BROKEN（公平性） | filter_correction_request.md → S3_ORACLE_MERGE | filter_iter |
| BROKEN（spec gap） | spec_patch_request.md（type=spec_gap）→ S2_SPEC_DRAFT → S3_ORACLE_MERGE → S4_EVAL_RUN | spec_iter |
| BROKEN（spec error） | spec_patch_request.md（type=spec_error）→ S2_SPEC_DRAFT → S3_ORACLE_MERGE → S4_EVAL_RUN | spec_iter |
| QUALIFIED | 记录到 CANDIDATES.md，追加 weakness table，任务完成 | — |

### 循环终止

反馈循环在以下情况终止：
- 请求产物已更新且所有下游检查通过，**或**
- 根本原因确定需要退休候选

同一循环不解决超过 2 次 → 退休候选。

---

## 十、完整状态机流程

```
新任务
  │
  ▼
S1_SCREENING ──（reject）──────────────────────────────────► RETIRED
  │（keep）
  ▼
S1_SELECTED
  │
  ▼
S2_SPEC_DRAFT ◄──────────────────────────────────────────────┐
  │                                                           │ spec_gap / spec_error
  ▼                                                           │ （spec_iter += 1）
S2_SPEC_CHECK ──（任意一条失败）──► [spec_iter > 3] ──► RETIRED
  │（全10条通过）
  ▼
S2_SPEC_DONE
  │
  ▼
S3A_IMPORT_AUDIT
  │
  ▼
S3A_REWRITE
  │（丢弃 ≤50%）        │（丢弃 >50%）
  ▼                     ▼
S3A_FAIRNESS       S3B_TRIGGER（需 rewrite_audit.md 存在）
  │                     │
  ▼                     ▼
S3A_DUMMY          S3B_COVERAGE
  │（count ≥30）        │
  ▼                     ▼
S3A_DONE           S3B_GENERATE ◄──────────────────────────┐
  │                     │                                   │（< 95%，filter_iter += 1）
  └──────────┬──────────┘                                   │
             ▼                                     S3B_REFERENCE ──► S3B_DONE
       S3_ORACLE_MERGE ◄───────────────────────────────────────────────────────┐
             │                                                                  │ filter issue
             ▼                                                                  │（filter_iter += 1）
       S3_REFERENCE_RUN ──（< 100%）──► fix oracle ──► S3_ORACLE_MERGE（loop）
             │（= 100%）
             ▼
       S3_DONE
             │
             ▼
       S4_SETUP（需 reference_score.json 存在）
             │
             ▼
       S4_EVAL_RUN ◄─────────────────────────────────────────────────────────┐
             │                                                                 │ cheat/env
             ▼                                                                 │（eval_iter += 1）
       S4_ANALYSIS ──（饱和）──► S2_SPEC_DRAFT（spec_iter += 1）              │
             │（oracle 问题）──► S3_ORACLE_MERGE（filter_iter += 1）           │
             │（正常）                                                         │
             ▼                                                                 │
       S4_DONE                                                                 │
             │                                                                 │
             ▼                                                                 │
       S5_JUDGE ────────────────────────────────────────────────────────────►─┘
             │                                                      CHEAT_DETECTED
             │（spec gap/error，spec_iter += 1）──► [> 3] ──► RETIRED
             │（filter issue，filter_iter += 1）──► [> 2] ──► RETIRED
             │（不可修复）──────────────────────────────────────► RETIRED
             │（所有 gate 通过）
             ▼
        QUALIFIED ✓
```

---

## 十一、全流程产出物清单

| 阶段 | 产出物 | 路径 | 说明 |
|------|--------|------|------|
| Stage 1 | `filter_notes.md` | `wip/{task}/` | 候选证据记录，所有字段必填 |
| Stage 1 | CANDIDATES.md 条目 | `Bmk-dev/` | SELECTED / RETIRED 行 |
| Stage 2 | `spec_vN.md` | `wip/{task}/spec/` | 通过11项验证后方为有效 |
| Stage 2 | `spec_patch_request.md` | `wip/{task}/spec/` | 来自 judge 的反馈，含 type 字段 |
| Stage 3 | `rewrite_audit.md` | `wip/{task}/filter/` | S3B_TRIGGER 的硬性前置 |
| Stage 3 | `rewritten_upstream_tests.py` | `wip/{task}/filter/` | 改写后的上游测试代码（非仅审计记录） |
| Stage 3 | `candidate_filter_map.md` | `wip/{task}/filter/` | 草稿阶段的 nodeid 状态表 |
| Stage 3 | `kept_upstream.txt` | `wip/{task}/filter/` | Track A 保留的 nodeids |
| Stage 3 | `coverage.json` | `wip/{task}/filter/` | Branch coverage 数据 |
| Stage 3 | `coverage_gaps.txt` | `wip/{task}/filter/` | 未覆盖分支（供生成 agent 使用） |
| Stage 3 | `generated_tests.py` | `wip/{task}/filter/` | Track B 生成的测试 |
| Stage 3 | `spec_test_map.md` | `wip/{task}/filter/` | 最终 oracle 映射表（含 source 列） |
| Stage 3 | `kept_nodeids.txt` | `wip/{task}/filter/` | 最终可评分 nodeid 列表 |
| Stage 3 | `taxonomy.jsonl` | `wip/{task}/filter/` | 评分器格式的层级分类 |
| Stage 3 | `reference_score.json` | `wip/{task}/filter/` | Reference 对 oracle 的运行结果（必须 100%） |
| Stage 3 | `filter_correction_request.md` | `wip/{task}/filter/` | 来自 judge 的过滤器修正请求 |
| Stage 4 | `score_result.json` | `candidate-runs/{run}/` | 候选 agent 评估结果 |
| Stage 5 | `diagnosis_report.md` | `wip/{task}/judge/` | 含 Preflight output 块 + Gate D 节 |
| 完成 | 任务目录 | `tasks/{task-id}/` | 从 wip/ 复制的关键产物 |
| 完成 | weakness_table.md 条目 | `Bmk-dev/` | 每个真实模型失败一行 |

### PIPELINE_STATE.md 关键字段说明

| 字段 | 含义 | 设置时机 |
|------|------|---------|
| `functions_in_scope` | 所有保留文件中的测试函数总数 | S3A Step 1 完成时，只写一次，此后只读 |
| `functions_kept` | `rewritten_upstream_tests.py` 中的函数数量 | S3A Step 3 完成时 |
| `functions_excluded` | `candidate_filter_map.md` 中 excluded 行数 | S3A Step 3 完成时 |
| `oracle_count` | `spec_test_map.md` 中 covered 行总数 | S3_ORACLE_MERGE 完成时；< 50 不得推进 |
| `spec_iter` | spec 循环计数 | 每次回 S2_SPEC_DRAFT 时 +1；> 3 → RETIRED |
| `filter_iter` | filter 循环计数 | 每次回 S3_ORACLE_MERGE 时 +1；> 2 → RETIRED |
| `eval_iter` | eval 循环计数 | 每次回 S4_SETUP 时 +1；> 2 → RETIRED |

---

## 十二、常见失败模式与处理

| 现象 | 根因 | 处理方式 |
|------|------|---------|
| 候选 collection 全部失败（0分） | spec 缺少一个公开导入路径 | 返回 spec-writer，补充缺失路径（见实验：缺失 `utils.sqlite3` → 100% collection failure） |
| 大量测试 spec_section 映射不到 spec 任何节 | test-filter 未真正做 spec 对照，批量填写了虚构的 section | 返回 test-filter，逐行重新核验 |
| 候选 pass rate = 100% 但实现文件数远少于原包 | 可能是训练数据召回而非真正重建 | 标记 trivially-solved + saturated-candidate-score；考虑加强 spec |
| integration/system_e2e 失败全都能被少数几个 atomic 失败解释 | 级联失败非组合失败 | weakness table 记录根因 atomic 失败，不记录级联失败 |
| Track A 改写后 >50% 文件被丢弃 | import 饱和（库内部结构被测试大量依赖） | 提前触发 Track B；在 `rewrite_audit.md` 记录所有失败原因 |
| Reference gate < 95%（Track B） | 生成的测试断言了 reference 实际不产生的行为 | 返回生成 agent 修正失败测试；`filter_iter += 1` |
| Preflight 输出指向系统安装包 | 评估环境隔离不足 | 使用 `--remove-path <pkg>`；重跑评估 |

