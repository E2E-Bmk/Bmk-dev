# Spec2Repo 规格说明标准（Specification Standard）

本文档定义 spec.md 的结构、每节作用、信息深度标准、以及 spec-oracle 对齐规则。
是编写 spec、编写 oracle、以及验收检查的唯一前置依据。

---

## 一、前置标准：信息深度划线

在写 spec 之前，先明确一条客观判据：

> **"一个只有 pip install 和 Python REPL 的开发者，不看源码，能不能发现这个信息？"**
>
> 能发现 → 属于公开 API，应写入 spec
> 不能发现 → 属于实现细节，不应写入 spec

具体划线：

？


| 信息类型            | 确定方法                             | 进 spec       |
| --------------- | -------------------------------- | ------------ |
| 模块路径            | `import X.Y` 成功                  | ✅            |
| 类/函数名           | `dir(module)` 非下划线               | ✅            |
| 方法/属性名          | `dir(class)` 非下划线                | ✅            |
| 参数名             | `inspect.signature()` 或 `help()` | ✅ 在行为描述中按需提及 |
| 参数值域            | 运行代码可观测                          | ✅ 列出合法取值     |
| 返回值的公开属性/key    | 运行代码 + `dir()`                   | ✅            |
| 错误条件 + 异常类型     | 运行代码可触发                          | ✅            |
| 参数类型注解          | 需看源码或 type stub                  | ❌            |
| 参数默认值           | 需看源码或 `inspect`                  | ❌            |
| 内部算法/数据结构       | 需看源码                             | ❌            |
| 私有方法/属性（`_xxx`） | 下划线开头                            | ❌            |
| 错误消息原文          | 不稳定、可变                           | ❌            |
| `__repr__` 格式   | 展示细节                             | ❌            |


---

## 二、Spec 结构定义

spec.md 按六个层次组织，每个层次承担一个明确职责。
文档中各节必须按此顺序排列。

```
═══ Context 层 ═══  回答"这是什么？边界在哪？"
  § Product Overview
  § Non-Goals

═══ Orientation 层 ═══  回答"怎么用？"
  § Representative Workflows

═══ Behavior 层 ═══  回答"每个接口做什么？"（spec 的核心）
  § {领域章节 1}
  § {领域章节 2}
  § ...（≥ 2 个，自由命名）

═══ Contract 层 ═══  回答"什么必须永远成立？"
  § State Model
  § Error Semantics
  § Cross-View Invariants

═══ Reference 层 ═══  回答"暴露什么给外界？"
  § Public Interface
    ├ Import Surface
    ├ API Catalog
    └ CLI Entry Points（仅 CLI 工具需要）

═══ Meta 层 ═══  Benchmark 专属信息（非 SDD 内容）
  § Appendix A: Environment
  § Appendix B: Assessment Notes
```

---

## 三、每节详细说明

### Context 层

#### § Product Overview


| 项目     | 说明                                                |
| ------ | ------------------------------------------------- |
| **作用** | 一段话定义产品核心职责，让读者 30 秒判断 spec 是否相关                  |
| **必需** | 是                                                 |
| **长度** | 1-3 段                                             |
| **写法** | "{Name} is a {category} that {core verb phrase}." |


示例（bandit）：

> Bandit is a local security linter for Python source. It parses each
> selected source file, applies installed security rules to the syntax
> tree, records issues and scan metrics, and projects that state through
> a command exit status and one selected report format.

#### § Non-Goals


| 项目     | 说明                                                            |
| ------ | ------------------------------------------------------------- |
| **作用** | 明确 spec 不覆盖的内容，划出实现边界                                         |
| **必需** | 是                                                             |
| **写法** | Bullet list，每条以 "This specification does not require/define..." 开头 |


示例（requests-cache）：

> - This specification does not require Redis, MongoDB, DynamoDB backends (require external services).
> - This specification does not require private helper modules and internal field layout.
> - This specification does not require exact `repr()` formatting and log message text.

**原则**：Non-Goals 中未列出的功能如果也未在 Behavior 层描述，默认视为不在范围内。

---

### Reference 层

#### § Public Interface


| 项目     | 说明                                                            |
| ------ | ------------------------------------------------------------- |
| **作用** | 声明包的全部公开入口——可 import 的符号、API 元素、CLI 命令                        |
| **必需** | 是                                                             |
| **子节** | Import Surface（必需）、API Catalog（必需）、CLI Entry Points（仅 CLI 工具） |


##### Import Surface


| 项目     | 说明                    |
| ------ | --------------------- |
| **作用** | 列出用户可 import 的模块和顶层符号 |
| **写法** | 用代码块列出 import 语句      |
| **深度** | 只列名称，不带类型注解           |


示例：

```python
from requests_cache import (
    CachedSession, CacheMixin, BaseCache,
    install_cache, uninstall_cache, enabled, disabled,
    NEVER_EXPIRE, EXPIRE_IMMEDIATELY, DO_NOT_CACHE,
)
```

##### API Catalog


| 项目     | 说明                                   |
| ------ | ------------------------------------ |
| **作用** | 每个公开类/函数/常量的**名称和一句话职责**，不含签名        |
| **写法** | 表格或列表，每项一行                           |
| **深度** | 名称 + 职责。参数名不在这里列，而是在 Behavior 章节按需出现 |


示例：

```
| Name            | Kind     | Role                                     |
|-----------------|----------|------------------------------------------|
| CachedSession   | class    | requests.Session subclass with caching   |
| install_cache   | function | Monkey-patch requests.Session globally   |
| BaseCache       | class    | Base class for cache backends             |
| CachedResponse  | class    | Response object with cache metadata       |
| create_key      | function | Generate cache key from a request         |
| NEVER_EXPIRE    | constant | Sentinel for no-expiration policy         |
```

**禁止**在 API Catalog 中出现的：

```python
# ❌ 完整签名
CachedSession(cache_name="http_cache", backend=None, expire_after=-1, ...)

# ❌ 类型注解
def install_cache(cache_name: str, backend: str | None = None) -> None:
```

##### CLI Entry Points（仅 CLI 工具需要）


| 项目     | 说明                   |
| ------ | -------------------- |
| **作用** | 声明 CLI 命令名、子命令、退出码含义 |
| **必需** | 仅当包提供 CLI 工具时        |
| **写法** | 命令名 + 用途 + 退出码表      |


示例（bandit）：

```
Console scripts: bandit, bandit-config-generator, bandit-baseline

| Exit | Meaning |
|-----:|---------|
| 0    | No reportable issue, or --exit-zero |
| 1    | One or more findings survive filtering |
| 2    | Usage, config, or setup failure |
```

对于纯库（如 requests-cache、attrs），此子节省略。

---

### Behavior 层

#### § {领域章节} （自由命名，≥ 2 个）


| 项目     | 说明                        |
| ------ | ------------------------- |
| **作用** | spec 的核心——描述系统在各种条件下的行为合约 |
| **必需** | 至少 2 个领域章节                |
| **写法** | 每个章节围绕一个功能领域，用行为条款组织      |


**行为条款的写法标准**：

每个条款应可映射为一个可测试的 assert。推荐使用 EARS 风格，但不强制格式：

```
WHEN force_refresh=True,
  the session SHALL send a new request and overwrite the existing cached entry.

WHEN the origin adapter raises and no stale response is permitted,
  the session SHALL re-raise the original exception.
```

等价的自然语言也可以：

```
If force_refresh is enabled, the session sends a new request
and overwrites the existing cached entry.
```

**参数名在这里按需出现**（不是在 API Catalog 里列签名）：

```
CachedSession 接受 backend 参数，可以是 "memory", "sqlite",
"filesystem" 之一，或一个 BaseCache 实例。
当 backend 为未知字符串时，init_backend 抛出 ValueError。
```

**领域章节的命名建议**：

按功能切分，不按类/文件切分。好的命名：

- Session Caching Behavior（围绕"缓存命中/未命中"）
- Request Matching（围绕"如何判断两个请求等价"）
- Expiration and Cache-Control（围绕"过期策略"）

不好的命名：

- CachedSession Methods（按类组织，不是按功能）
- utils.py Functions（按文件组织）

---

### Contract 层

#### § State Model


| 项目     | 说明                               |
| ------ | -------------------------------- |
| **作用** | 定义系统的状态空间和公开投影（可观测的视图）           |
| **必需** | 是。纯函数库（无持久状态）可简化为"数据流模型"         |
| **写法** | "系统维护 X 状态，通过 Y1、Y2、Y3 三个投影对外可见" |


有状态系统示例（requests-cache）：

> The core state is a set of cached response entries. Each entry is keyed
> by normalized request data. The public projections are:
>
> 1. Session request results (from_cache, created_at, expires)
> 2. Backend mapping (session.cache.responses, session.cache.redirects)
> 3. Patcher state (is_installed(), get_cache())

无状态/纯函数库示例（packaging）：

> The package exposes stateless parsing and comparison operations.
> A Version or Requirement constructed from a string must produce
> deterministic comparison, hashing, and string round-trip results.
> There is no mutable shared state.

#### § Error Semantics


| 项目     | 说明                |
| ------ | ----------------- |
| **作用** | 条件 → 预期结果的错误处理合约表 |
| **必需** | 是                 |
| **写法** | 表格：条件             |


示例：

```
| Condition                        | Required result              |
|----------------------------------|------------------------------|
| Unknown backend alias            | Raise ValueError             |
| Invalid HTTP date string         | Raise ValueError             |
| only_if_cached on miss           | Return 504 response          |
| Origin request raises, no stale  | Re-raise original exception  |
```

**规则**：只指定异常类型，不指定消息文本。

#### § Cross-View Invariants


| 项目     | 说明                                                |
| ------ | ------------------------------------------------- |
| **作用** | 跨模块/跨操作必须成立的一致性约束。直接映射为 integration/system_e2e 测试 |
| **必需** | 是                                                 |
| **写法** | 编号列表，每条是一个可验证的不变量                                 |


示例：

> 1. A response cached through `CachedSession.get()` must be discoverable
>   through `session.cache.contains(url=...)`.
> 2. A response deleted through `session.cache.delete()` must no longer be
>   returned as a cache hit.
> 3. Installing the patcher must make `requests.Session()` use the active cache;
>   uninstalling must restore original behavior.

**每条不变量应直接对应至少一个 integration 测试。**

---

### Orientation 层

#### § Representative Workflows


| 项目     | 说明                          |
| ------ | --------------------------- |
| **作用** | 2-3 个端到端代码示例，验证 spec 可读、可实现 |
| **必需** | 是，≥ 2 个                     |
| **写法** | 代码 + 一段话解释预期行为              |


**关键定位**：Workflows 不是 oracle 测试的依据。oracle 的依据是 Behavior 章节和 Contract 层。Workflows 的作用是：

1. 帮助读者快速理解产品用法
2. 验证 spec 作者自己能把 spec 走通
3. 提供给模型作为"如何使用"的参考

---

### Meta 层（Benchmark 专属）

#### § Appendix A: Environment


| 项目     | 说明                         |
| ------ | -------------------------- |
| **作用** | 声明评测环境的 Python 版本、预装包、网络限制 |
| **必需** | 是                          |
| **写法** | 固定模板                       |


模板：

> The working environment runs Python 3.11 on Linux without network access.
> The following third-party packages are preinstalled and importable:
> {requirements.txt 中的包名列表}.
> The assessment environment provides the same interpreter and package set.
>
> The project must declare its packaging metadata in a standard
> `pyproject.toml` (or `setup.py`) at the project root so the package
> can be installed with pip.

#### § Appendix B: Assessment Notes


| 项目     | 说明               |
| ------ | ---------------- |
| **作用** | 告诉模型评分关注什么，不关注什么 |
| **必需** | 是                |
| **写法** | 简短说明评分视角         |


---

## 四、Spec-Oracle 对齐规则

### 工作流

```
上游项目 ──→ 前置标准(§一) ──→ Spec ──→ Oracle ──→ 对齐检查 ──→ 微调
                                  ▲                      │
                                  └──────────────────────┘
```

### Oracle 编写规则

1. 每个测试函数追溯到 **Behavior 章节或 Contract 层**的某个条款（不是 Workflows）
2. 每个 assert 使用的标识符（类名、方法名、属性名、参数名、dict key）必须在 spec 中出现过
3. 期望值通过**实际运行上游代码**获取，不猜

### 对齐检查：四种"对不上"


| 类型           | 表现                                                        | 修法                                                      |
| ------------ | --------------------------------------------------------- | ------------------------------------------------------- |
| **A: 名称未声明** | oracle assert 了 `response.cache_key`，spec 未提及 `cache_key` | 查上游：公开属性 → 补 spec；私有属性 → 改 oracle                       |
| **B: 行为未描述** | oracle 测了 `force_refresh` 行为，spec 没有相关条款                  | 查上游：有此功能 → 补 Behavior 条款；无此功能 → 删 oracle                |
| **C: 条款未覆盖** | spec 描述了 `stale_while_revalidate` 行为，oracle 没有测试          | 可测 → 补 oracle；不可测 → 条款标注 `(non-testable)` 或移入 Non-Goals |
| **D: 期望值矛盾** | spec 说 "exit 1"，oracle assert `returncode == 0`           | 以上游实际行为为准，修正错误的一方                                       |


### 微调优先级

1. **优先补 spec**（让 spec 更完整）
2. **其次改 oracle**（如果测试超纲或猜值）
3. **最后删条款**（如果行为不可测）

---

## 五、与当前 11 节结构的映射


| 当前章节                     | 目标位置                                    | 变化              |
| ------------------------ | --------------------------------------- | --------------- |
| Product Overview         | § Product Overview (Context)            | 不变              |
| Scope / Non-Goals        | § Non-Goals (Context)                   | 合并为 Non-Goals   |
| Representative Workflows | § Representative Workflows (Orientation) | **提前到 Context 后** |
| {自由章节 1..N}              | § Behavior 层 {领域章节}                     | **要求 ≥ 2 个**    |
| Product State Model      | § State Model (Contract)                | 不变              |
| Error Semantics          | § Error Semantics (Contract)            | 不变              |
| Cross-View Invariants    | § Cross-View Invariants (Contract)      | 不变              |
| Installable Surface      | § Public Interface > Import Surface     | 归入 Reference 层  |
| Public API (42/51 有)     | § Public Interface > API Catalog        | **提升为必需**       |
| Invocation Protocol      | § Public Interface > CLI Entry Points   | 归入子节，纯库省略       |
| Environment              | § Appendix A: Environment (Meta)        | 移入附录            |
| Implementation Guidance  | § Appendix B: Assessment Notes (Meta)   | 移入附录，改名         |


### 总节数对比


|             | 当前  | 目标         |
| ----------- | --- | ---------- |
| 必需节（固定）     | 11  | 9（含 3 个子节） |
| 必需行为节（自由命名） | 0   | ≥ 2        |
| 总最低节数       | 11  | 11         |


结构复杂度持平，但语义更清晰：每个节的职责不交叉，Behavior 层有最低保障。

**实际节顺序**（从上到下）：Product Overview → Non-Goals → Representative Workflows → {Behavior 章节} → State Model → Error Semantics → Cross-View Invariants → Public Interface → Appendix A → Appendix B