# Spec2Repo Oracle 质量标准（Oracle Quality Standard）

本文档定义 oracle 测试套件的结构、层级分离、覆盖要求、断言规范和区分力门槛。
是编写 oracle、审查 oracle、以及验收 oracle 的唯一前置依据。

与 `SPEC_STANDARD.md` 形成闭环：Spec 定义"要测什么"，本标准定义"怎么测、测到什么程度"。

---

## 一、结构要求

### 文件组织

每个 task 的 oracle 目录必须包含：

```
oracle/{task_id}/
├── conftest.py          # 共享 fixtures、helpers、常量
├── test_atomic.py       # 原子层测试
├── test_integration.py  # 集成层测试
├── requirements.txt     # 测试依赖
└── fixtures/            # （可选）外部测试数据文件
```

**conftest.py 是必需的。** 规则：

- 两个测试文件中出现的相同 helper 函数、相同 fixture、相同常量、相同 import 块，
  必须提取到 `conftest.py`
- 这不是代码风格偏好，而是维护性要求——重复代码在修改 spec 时会产生
  不一致的更新风险

### 测试数量底线

基于现有 51 个 task 的实际分布（atomic 中位数 27、integration 中位数 35、总数中位数 68），
底线设定需保证 gap 指标的统计稳定性。

| 层级 | 最低数量 | 依据 |
|------|---------|------|
| Atomic | ≥ 20 | 单个测试对 atomic_rate 的影响 ≤ 5pp |
| Integration | ≥ 20 | 单个测试对 integ_rate 的影响 ≤ 5pp |
| **总计** | **≥ 50** | 单个测试对总通过率影响 ≤ 2pp |

**统计依据**：gap = atomic_rate − integration_rate，涉及两个独立维度。
单个 atomic 测试翻转对 gap 的最大影响 = 1/N_atomic，
单个 integration 测试翻转对 gap 的最大影响 = 1/N_integration。
当 N_atomic = N_integration = 20 时，gap 的单测试分辨率 = 5pp——
恰好匹配观测到的跨模型 gap 量级（多数在 3–12pp）。
低于此值，单个偶然通过/失败即可制造 "虚假 gap"。

总数 ≥50 的约束确保即使两层分配不均（如 25/25 或 30/20），
整体通过率仍有 ≤2pp 的分辨率，不受单测试偶然性左右。

**现有 task 达标情况**：51 个 task 中 8 个 atomic <20（需补测试），
1 个 integration <20（需补测试），总数全部 ≥50（已达标）。

---

## 二、Claim-Driven 设计原则

Oracle 不是通用测试套件。它的唯一目的是支撑 Spec2Repo 的核心 claim：

> **"模型写单个组件比组装系统强"——Integration Gap 是跨模型的普遍现象。**

为了让这个 claim 在论文审稿中经得起挑战，oracle 的设计必须满足以下四条原则。
**所有后续的结构、层级、覆盖、断言规则都是这四条原则的具体展开。**

### 原则 1：独立可解性（Independent Solvability）— 约束 Atomic

> 如果模型只正确实现了被测的这一个 API（其他全是 stub），
> 对应的 atomic 测试就应该能通过。

这确保 atomic_rate 度量的是"实现单个行为的能力"，而不是"同时做对多件事的能力"。
违反此原则的测试混入 atomic 层会压低 atomic_rate，人为缩小 gap。

**检验方法**：对每个 atomic 测试问——"如果只有这一个函数是真实实现，
其余全部 raise NotImplementedError，这个测试能过吗？"
答案为"不能"→ 该测试属于 integration。

### 原则 2：组合依赖性（Composition Dependency）— 约束 Integration

> 即使模型的所有 atomic 测试全部通过，
> 一个 integration 测试仍然可能失败——因为组件之间的"接缝"没对上。

这确保 integration_rate 度量的是"正确组装的能力"，
而不是"实现更多代码的能力"。违反此原则的测试是"伪 integration"——
它不提供超出 atomic 的额外信号，只是让 integration_rate 追随 atomic_rate，
人为缩小 gap。

**检验方法**：对每个 integration 测试问——"存不存在一种实现，
让所有 atomic 测试通过，但这个 integration 测试失败？"
答案为"不存在"→ 该测试是伪 integration，应降级为 atomic 或删除。

### 原则 3：接缝靶向（Seam Targeting）— 指导 Integration 的选题

Integration 测试应该精准瞄准组件之间的"接缝"（composition seams），
而不是简单地把多个 API 调用串在一起。

五种典型接缝：

| 接缝类型 | 失败意味着 | 示例 |
|---------|----------|------|
| **状态一致性** | API-A 写入的状态，API-B 读不到或读错 | session.get() 写缓存 → cache.contains() 查不到 |
| **协议交接** | 组件 A 的输出格式不是组件 B 的合法输入 | key 生成模块产出的 key，backend 无法正确存取 |
| **错误传播** | 组件 A 的异常没被调用链中的组件 B 正确处理 | origin 超时 → stale_if_error 应返回过期缓存而非崩溃 |
| **配置交互** | 一处配置影响多个组件，但组件间没同步 | ignored_parameters 影响 key 生成但没影响存储 redaction |
| **生命周期跨越** | 创建→关闭→重开，持久状态丢失或损坏 | SQLite session close → 新 session 读不到旧缓存 |

每个 integration 测试应该能明确归入至少一种接缝类型。
如果一个测试说不清它在测哪条接缝，它很可能是伪 integration。

### 原则 4：Anti-Memorization — 防止记忆替代能力

测试中的具体参数值必须避开上游库自身测试用例中的值。

| 做法 | 原因 |
|------|------|
| 上游用 `expire_after=300`，oracle 用 `expire_after=60` | 同一行为，不同数值，记忆无法直接抄答案 |
| 上游用 `"test_key"`，oracle 用 `"cache-alpha"` | 避免字面匹配 |
| 上游按 method A→B→C 顺序测，oracle 按 C→A→B | 避免顺序记忆 |

**注意**：Anti-memorization 不是"故意制造陷阱"。测试的行为和 spec 描述完全一致，
只是具体参数值不同。模型如果真正理解了 spec 描述的行为，使用什么参数值都应该能通过。

### 核心推论：条件通过率

四条原则共同指向一个最能支撑 claim 的衍生指标：

> **条件通过率** = P(integration_pass | 所有 depends_on 的 atomic 均 pass)

这是纯粹的"会写零件但不会拼"的度量。计算前提是 integration 测试标注了
`depends_on`（见§三），这也是为什么 depends_on 不仅是"推荐"而是应当尽力标注。

---

## 三、层级分离标准

这是 oracle 设计中最关键的决策。Spec2Repo 的核心指标 Integration Gap 完全建立在
层级标签之上——标签错，指标就没有意义。

### Atomic 层定义

**一个 atomic 测试验证单个公共 API 入口的单个行为点。**

准入条件（全部满足才能放入 `test_atomic.py`）：

1. 只调用一个被测公共函数/方法/类（setup 阶段的辅助调用不算）
2. 验证的行为可以用一句话描述："当 X 时，Y 应该返回/抛出 Z"
3. 不依赖另一个公共 API 的正确实现来产生可观测的断言
4. 如果被测 API 的实现是一个 stub（只做该 API 自己的事），测试应该能通过

**反例（不应放入 atomic）：**

- 通过 `session.get()` 写入缓存，然后通过 `session.cache.contains()` 验证——
  这跨了 Session API 和 Backend API 两个边界
- 先 `install_cache()` 再 `requests.get()` 再检查 `is_installed()`——
  这是三个 API 的协作

### Integration 层定义

**一个 integration 测试验证 ≥2 个不同公共 API 边界的协作。**

准入条件（至少满足一条）：

1. **写→读跨边界**：通过 API-A 写入状态，通过 API-B 读取/验证状态
2. **生命周期跨越**：创建对象→关闭→重新打开→验证持久化
3. **策略组合**：多个独立配置项组合后产生的涌现行为
4. **上下文嵌套**：context manager 的进入/退出对其他 API 行为的影响

**Integration 测试的黄金标准**：如果被测系统中某一个模块是 stub，这个测试应该会失败。

### 层级分离的轨迹验证信号

以下信号来自实际评测轨迹，用于验证层级分离是否正确：

| 信号 | 含义 | 处置 |
|------|------|------|
| 跨模型平均 gap < -5pp | atomic 比 integration 更难通过 | **必须审查**：atomic 中可能混入了跨模块测试，或 integration 中存在伪集成（实质是 atomic）|
| 跨模型平均 gap ≈ 0 且强模型接近满分 | integration 未真正测试协作能力 | **应审查**：检查 integration 是否只是"更长的 atomic" |
| 某模型 gap 极大 (>30pp) 但其他模型 gap 正常 | 该模型特定弱点，非标签问题 | 正常，无需处置 |
| 所有模型 gap 均为大正值 (>15pp) | integration 真正在测系统设计能力 | 理想状态 |

### depends_on 标注（推荐）

每个 integration 测试应标注它依赖哪些 atomic 行为，格式：

```python
@pytest.mark.depends_on("test_cache_set_returns_true", "test_cache_get_returns_stored_value")
def test_cache_persists_across_reopened_objects(tmp_path):
    ...
```

这使得以下分析成为可能：
- 条件通过率：依赖的 atomic 全过但 integration 仍挂的比例（纯系统设计缺陷）
- 层级标签审计：如果 integration 测试不依赖任何 atomic，它可能是伪集成

---

## 四、Spec-Oracle 覆盖要求

### 上游测试作为启发源（非搬运源）

编写 oracle 时，必须阅读上游原始仓库的测试代码作为启发。原因：

1. **LLM 猜不全面**——上游库的作者最了解哪些边界条件真正重要
2. **期望值来自运行**——oracle 中的 assert 值必须通过实际运行上游代码获取，不猜
3. **接缝位置来自实战**——上游测试中失败率最高的测试往往指向真正的接缝

**⚠️ 核心警告：上游测试大量依赖私有 API，不能直接搬运。**

上游库的测试通常这样写：

```python
# 上游测试（依赖私有 API，不可用于 oracle）
from requests_cache._utils import _normalize_dict
from requests_cache.backends._sqlite import _get_connection

def test_normalize_dict_sorts_keys():
    assert _normalize_dict({"b": 2, "a": 1}) == {"a": 1, "b": 2}
```

这里 `_normalize_dict` 和 `_get_connection` 是下划线开头的私有函数。
Oracle **绝对不能**测试这些。但这个测试告诉我们一个有价值的信息：
**"字典参数的排序对缓存 key 有影响"**——这个行为洞察可以转化为公开 API 的测试：

```python
# Oracle 测试（同一行为洞察，通过公开 API 验证）
def test_query_parameter_order_does_not_affect_cache_key():
    req1 = requests.Request("GET", "https://example.test/items?b=2&a=1").prepare()
    req2 = requests.Request("GET", "https://example.test/items?a=1&b=2").prepare()
    assert create_key(req1) == create_key(req2)
```

**提取流程（三步转化法）**：

```
上游测试 ──→ 提取行为洞察 ──→ 检查 spec 是否覆盖 ──→ 用公开 API 重写
                │                    │                      │
          "什么边界条件       是 → 写 oracle          必须通过公开 API
           是重要的？"      否 → 跳过（spec 未描述     验证，绝不引用
                               的行为不测）           下划线符号
```

**信息粒度过滤规则**（与 `SPEC_STANDARD.md` §一 前置标准对齐）：

| 上游测试中的元素 | Oracle 是否可用 | 判据 |
|----------------|:---:|------|
| 公开函数/方法名（`dir()` 可见、无下划线） | ✅ | spec 中已列出 |
| 公开属性名（`dir(obj)` 可见） | ✅ | spec 中已列出 |
| 公开异常类型 | ✅ | spec Error Semantics 已列出 |
| 私有函数 `_xxx` / `__xxx` | ❌ | `dir()` 过滤后不可见 |
| 私有模块 `pkg._internal.xxx` | ❌ | 内部布局是实现细节 |
| 内部数据结构（如 SQLite 表结构） | ❌ | 存储方式是实现细节 |
| 调试/日志接口 | ❌ | 非公开合约 |
| `conftest.py` 中的 mock/patch 内部类 | ❌ | 依赖实现细节 |

**实操建议**：

1. 先扫描上游测试目录，列出所有 `test_*.py` 文件
2. 按文件浏览测试函数名——函数名本身就是行为洞察的索引
3. 对每个有价值的测试，问三个问题：
   - 这个行为 spec 里有吗？（没有 → 跳过）
   - 能否只用公开 API 验证？（不能 → 跳过或寻找等价的公开路径）
   - 期望值能否通过 `pip install` + REPL 复现？（不能 → 跳过）
4. 通过筛选的测试，用不同参数值重写（Anti-Memorization）

### 覆盖方向

| 方向 | 要求 | 验证方法 |
|------|------|---------|
| Spec → Oracle | Spec 每个 Behavior 章节至少 2 个 atomic 测试 | 按章节计数 |
| Spec → Oracle | Spec 每条 CVI 至少 1 个 integration 测试 | 按 CVI 编号计数 |
| Spec → Oracle | Error Semantics 每行至少 1 个测试 | 按行计数 |
| Oracle → Spec | 每个测试函数可追溯到 spec 的具体条款 | 人工标注或 naming convention |

**覆盖率底线**：

- Behavior 章节覆盖率（有测试的章节 / 总章节）≥ 90%
- CVI 覆盖率（有测试的 CVI / 总 CVI）= 100%
- Error Semantics 覆盖率（有测试的条目 / 总条目）≥ 80%

### 未覆盖条款的处理

如果 spec 中某个行为确实无法测试（如"应支持自定义序列化器"这种需要运行时环境的行为），
必须在该条款后标注 `(non-testable)` 并在 spec 的 Non-Goals 中说明原因。
**不允许"spec 写了但默默不测"。**

---

## 五、行为纯粹性

### 禁止检查的内容

| 类别 | 示例 | 原因 |
|------|------|------|
| `repr()` / `__str__()` 输出 | `assert repr(obj) == "Foo(bar=1)"` | 文本表示是实现细节 |
| 精确错误消息文本 | `assert str(e) == "invalid key"` | 消息措辞是实现细节 |
| 私有属性 | `assert obj._internal_state == 3` | 下划线开头 = 非公开 |
| 内部数据结构 | `assert isinstance(obj._store, dict)` | 存储方式是实现细节 |
| 精确日志/警告文本 | `assert "WARNING: ..." in caplog.text` | 日志措辞不是合约 |
| 模块内部布局 | `import pkg._internal.helper` | 子模块组织是实现细节 |

### 允许检查的内容

| 类别 | 示例 | 条件 |
|------|------|------|
| 返回值 | `assert fn(x) == expected` | spec 描述了此行为 |
| 公开属性 | `assert obj.cache_key is not None` | spec 中出现过该属性名 |
| 异常类型 | `pytest.raises(ValueError)` | spec Error Semantics 指定了该类型 |
| 副作用 | `assert len(cache.responses) == 0` | spec 描述了该可观测状态 |
| 文件存在 | `assert path.exists()` | spec 描述了持久化行为 |

### 异常类型精度

- **必须**：`pytest.raises(ValueError)` 或 `pytest.raises((ValueError, TypeError))`
- **禁止**：`pytest.raises(Exception)` — 过宽的异常捕获无法区分正确失败和意外崩溃

---

## 五、断言质量

### 反模式清单（Anti-Pattern Checklist）

以下模式在 oracle 中**严格禁止**。这不是建议，是硬性规则。

| 编号 | 反模式 | 示例 | 为什么禁止 | 正确写法 |
|------|--------|------|-----------|---------|
| AP-1 | isinstance 作为唯一断言 | `assert isinstance(result, dict)` | 空字典、错误内容也能通过 | 追加值断言：`assert isinstance(r, dict); assert "key" in r` |
| AP-2 | `assert True` | `result = fn(); assert True` | 恒真，无区分力 | 断言返回值：`assert fn() == expected` |
| AP-3 | `pytest.raises(Exception)` | `with pytest.raises(Exception):` | 任何错误都能通过 | 用具体类型：`pytest.raises(ValueError)` |
| AP-4 | 只执行不断言 | `session.get(url)  # no assert` | 不检查任何行为 | 至少一个 `assert` |
| AP-5 | `assert x is not None` 作为唯一断言 | `assert fn() is not None` | 返回任何非 None 值均通过 | 追加具体检查：`r = fn(); assert r is not None; assert r.status == 200` |
| AP-6 | `assert len(x) > 0` 作为唯一断言 | `assert len(results) > 0` | 不检查内容 | `assert len(results) == 3; assert results[0].name == "x"` |
| AP-7 | 残留旧生成注释 | `"""Track B oracle from spec_v3"""` | 暴露生成过程 | 用标准 docstring：`"""Atomic tests for {task_id}."""` |

**每个测试函数中，AP-1 至 AP-6 违规 = 验收不通过。不存在例外。**

### 集成测试 Seam 标注要求

**每个 integration 测试函数必须在 docstring 中标注目标接缝类型。** 这是硬性要求，不是风格建议。

接缝类型关键词（至少使用一个）：

| 接缝类型 | 关键词 | 示例场景 |
|---------|--------|---------|
| 状态一致性 | `Seam: state consistency` | dump ↔ load 投影一致 |
| 协议交接 | `Seam: protocol handoff` | HTTP/1.1 → HTTP/2 升级 |
| 错误传播 | `Seam: error propagation` | 子模块异常 → 上层包装 |
| 配置交互 | `Seam: config interaction` | 环境变量 × 配置文件 × 默认值 |
| 生命周期跨越 | `Seam: lifecycle crossing` | 创建 → 使用 → 关闭 |
| 跨视图不变量 | `CVI-N:` | spec 中定义的 CVI |

**示例（正确写法）**：
```python
def test_dumps_and_loads_agree_with_dump_and_load():
    """Seam: state consistency between JSON serialization and direct projection."""
    ...
```

**示例（错误写法 — 无标注）**：
```python
def test_round_trip():  # ❌ 缺少 Seam 标注
    ...
```

**验收检查**：integration 测试文件中 ≥ 80% 的测试函数必须包含 Seam/CVI 标注。

### 断言分类

| 级别 | 定义 | 示例 | 接受度 |
|------|------|------|--------|
| **Positive** | 检查具体值 | `assert result == 42` | 首选 |
| **Relational** | 检查值关系 | `assert a < b` | 可接受（spec 只约束关系时） |
| **Type-check** | 只检查类型 | `assert isinstance(x, int)` | 仅当 spec 只约束类型时可接受 |
| **Existence** | 只检查非 None | `assert x is not None` | 仅作为复合断言的一部分 |
| **No-check** | 只执行不断言 | `fn(x)  # no assert` | **禁止** |
| **Tautology** | 恒真断言 | `assert x >= 0` (x 是 unsigned) | **禁止** |

**质量底线**：

- Positive + Relational 断言占比 ≥ 90%
- 每个测试函数至少有 1 个 Positive 或 Relational 断言
- 零个 No-check 测试
- 零个 Tautology 断言

### Failure-path 测试

错误路径测试（`pytest.raises`）视为 Positive 级别——它检查了具体的异常类型。
但必须搭配异常类型精度规则。

---

## 六、边界覆盖要求

### 每个 Behavior 章节的最低边界覆盖

| 路径类型 | 要求 | 示例 |
|---------|------|------|
| 正常路径 | ≥ 1 个测试 | 输入合法值，检查预期输出 |
| 边界值 | ≥ 1 个测试 | 空输入、零值、单元素、最大/最小值 |
| 错误路径 | ≥ 1 个测试（如果 spec 定义了错误行为）| 非法输入触发异常 |

### 必须覆盖的通用边界条件

以下条件如果 spec 中存在对应行为，必须有测试：

- 空集合操作（空 list/dict/set 作为输入）
- None 作为参数（如果 spec 区分 None 和缺省）
- 边界数值（0、-1、极大值）
- 重复操作（同一操作执行两次的幂等性）
- 缺失键/不存在的资源

### 边界覆盖的轨迹验证信号

| 信号 | 含义 | 处置 |
|------|------|------|
| 强模型（top-3）在某 task 达到 100% 通过率 | 测试集缺乏区分力 | **必须补充边界测试**直到 top-3 不全满分 |
| 空壳实现通过 >0 个测试 | 存在不检验真实行为的测试 | **必须修复或删除** |

---

## 七、区分力门槛（Dummy Gate 和 Reference Gate）

### Reference Gate（上界验证）

参考实现必须通过 100% 的 atomic 和 integration 测试。

验证方法：
```bash
pip install {reference_package}
pytest oracle/{task_id}/ --json-report
# 要求：passed == total
```

如果参考实现无法通过某个测试，该测试存在以下问题之一：
1. 测试期望值错误（以上游实际行为为准修正）
2. 测试依赖了 spec 描述但上游未实现的行为（删除测试或修正 spec）
3. 环境问题（修正 requirements.txt）

### Dummy Gate（下界验证）

一个只有空 `__init__.py` + 公开类/函数全部 raise `NotImplementedError` 的
空壳实现，必须通过 0% 的测试。

验证方法：生成 dummy 包 → pip install → pytest → 要求 passed == 0。

**如果 dummy 通过了任何测试**，该测试属于"水测试"（free point），必须修复：
- 通常原因：测试只检查了 import 成功或 isinstance，而没有检查行为
- 修法：添加行为断言

---

## 八、命名与组织规范

### 测试函数命名

格式：`test_{被测行为的动词短语}`

- 好：`test_cache_clear_removes_all_entries`
- 好：`test_invalid_backend_raises_value_error`
- 差：`test_cache_1`（无语义）
- 差：`test_it_works`（无具体行为）

名称应该让人不看代码就知道这个测试在验证什么行为。

### Fixture 命名

- `conftest.py` 中的 fixture 以 `_` 结尾表示 autouse：`cleanup_patcher`
- 非 autouse fixture 用名词命名：`tmp_cache_dir`、`mock_session`

### 常量

- 测试中反复使用的 URL、路径等常量提取到 `conftest.py` 顶层
- 格式：`URL = "https://example.test/data"`（使用 `.test` TLD 避免真实 DNS）

---

## 九、与 SPEC_STANDARD 的对齐关系

```
SPEC_STANDARD.md                    ORACLE_STANDARD.md
─────────────────                   ──────────────────
Behavior 章节 ──────────────────→ test_atomic.py（每章节 ≥2 个测试）
Error Semantics ────────────────→ test_atomic.py（每行 ≥1 个测试）
Cross-View Invariants ──────────→ test_integration.py（每条 ≥1 个测试）
State Model ────────────────────→ test_integration.py（投影一致性验证）
Representative Workflows ───────→ 不直接对应测试（仅辅助理解）
Product Overview / Non-Goals ───→ 不对应测试
Public Interface ───────────────→ 间接验证（import 在测试前言中）
```

### 对齐检查清单

在 oracle 编写完成后，逐项检查：

- [ ] 每个 Behavior 章节标题在 `test_atomic.py` 中有对应测试（可通过函数名搜索）
- [ ] 每条 CVI 在 `test_integration.py` 中有对应测试
- [ ] Error Semantics 中每个条目有对应的 `pytest.raises` 测试
- [ ] 每个测试 assert 使用的标识符（类名、方法名、属性名）在 spec 中出现过
- [ ] 没有测试检查 spec 未描述的行为
- [ ] conftest.py 消除了两个测试文件间的重复代码
- [ ] Reference Gate 通过（参考实现 100%）
- [ ] Dummy Gate 通过（空壳实现 0%）

---

## 十、来自评测轨迹的质量校准指引

以下规则来自对 10 个模型 × 36 个 task 的真实评测轨迹分析，
用于在 oracle 编写后进行校准。

### 负 Gap 审查规则

**当一个 task 的跨模型平均 gap < -5pp 时，必须执行以下审查：**

1. 逐个检查 `test_atomic.py` 中的测试，确认每个测试是否满足 atomic 准入条件
2. 逐个检查 `test_integration.py` 中的测试，确认每个测试是否真正跨越 ≥2 个 API 边界
3. 如果发现标签错误，重新归类并记录变更理由

已知需要审查的 task（基于历史轨迹数据）：

| Task | 历史平均 Gap | 问题假设 |
|------|-------------|---------|
| marshmallow-schema | -11.7pp | atomic 可能包含跨模块测试 |
| dvc | -11.6pp | atomic 可能测试了 CLI 端到端流程 |
| pelican-sitegen | -6.6pp | integration 可能是伪集成 |
| httpcore-transport | -5.8pp | 待分析 |
| vcrpy | -5.8pp | 待分析 |
| boltons-coreutils | -5.0pp | 待分析 |

### 天花板审查规则

**当 top-3 模型中有 ≥2 个在某 task 达到 100% 时，必须补充边界测试。**

已知需要审查的 task：

| Task | 信号 | 可能原因 |
|------|------|---------|
| diskcache | opus 100%/100% | 边界覆盖 3.5/5，缺少极端输入 |

### 水测试审查规则

**Dummy Gate 通过的测试必须全部修复或删除。**

已知需要审查的 task：

| Task | 信号 | 详情 |
|------|------|------|
| diskcache | 空壳通过 2/36 atomic | 存在不检验真实行为的测试 |

---

## 十一、验收流程

一个 oracle 通过验收需要满足以下全部条件：

### 硬性门（自动化可检查）

1. ✅ 文件结构完整（conftest.py + test_atomic.py + test_integration.py + requirements.txt）
2. ✅ Atomic ≥ 20 个测试函数
3. ✅ Integration ≥ 20 个测试函数
4. ✅ 总测试数 ≥ 50
5. ✅ Reference Gate 通过（参考实现 100%）
6. ✅ Dummy Gate 通过（空壳实现 0%）
7. ✅ 无 `pytest.raises(Exception)` — 异常类型必须具体
8. ✅ conftest.py 存在且非空

### 软性门（人工审查）

9. ✅ 每个 Behavior 章节有 ≥3 个 atomic 测试（正常 + 边界 + 错误）
10. ✅ 每条 CVI 有 ≥2 个 integration 测试（正向 + 边界/反向）
11. ✅ Error Semantics 覆盖率 ≥ 80%
12. ✅ Positive + Relational 断言占比 ≥ 90%
13. ✅ 零个 No-check / Tautology 断言
14. ✅ 每个 integration 测试真正跨越 ≥2 个 API 边界
15. ✅ 每个 atomic 测试只涉及 1 个 API 入口的 1 个行为点
16. ✅ 共享代码提取到 conftest.py，两文件间无重复 helper

### 校准门（需要轨迹数据，发布前检查）

17. ✅ 跨模型平均 gap > -5pp（否则触发负 gap 审查）
18. ✅ Top-3 模型未全部满分（否则触发天花板审查）
19. ✅ Dummy Gate 零通过（否则触发水测试审查）
