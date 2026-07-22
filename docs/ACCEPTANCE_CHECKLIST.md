# Spec2Repo 任务验收标准（Acceptance Checklist）

每个 task 在入库前必须逐项通过以下检查。检查人对每一项标注 ✅ PASS / ❌ FAIL。
出现任何 ❌ 则不可入库，修复后从头重走全部检查项。

本文档是项目的**唯一验收依据**，`QUALITY_GATE.md` 描述的是规则，
本文档描述的是**操作级的逐项检查动作和判定标准**。

---

## 一、文件完整性（5 项）

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 1.1 | `tasks/{id}/spec.md` 存在 | 文件存在且非空 |
| 1.2 | `tasks/{id}/task.json` 存在 | 文件存在且能被 `json.loads` 解析 |
| 1.3 | `oracle/{id}/test_atomic.py` 存在 | 文件存在且能被 `ast.parse` 解析 |
| 1.4 | `oracle/{id}/test_integration.py` 存在 | 文件存在且能被 `ast.parse` 解析 |
| 1.5 | `oracle/{id}/requirements.txt` 存在 | 文件存在 |

---

## 二、Spec 结构（11 项）

逐项确认 `spec.md` 包含以下 `##` 级章节（允许括号内别名）：

| # | 章节名 | 允许别名 |
|---|--------|----------|
| 2.1 | Product Overview | — |
| 2.2 | Scope | — |
| 2.3 | Installable Surface | Public Import Surface |
| 2.4 | Product State Model | Notebook JSON State Model |
| 2.5 | Error Semantics | Validation And Error Reporting |
| 2.6 | Cross-View Invariants | Cross-Component Invariants |
| 2.7 | Representative Workflow(s) | — |
| 2.8 | Non-Goals | — |
| 2.9 | Invocation Protocol | — |
| 2.10 | Environment | — |
| 2.11 | Evaluation Notes | Implementation Guidance |

---

## 三、Spec 内容质量（8 项）

### 信息泄漏检查

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 3.1 | 正文无禁用词 | spec 正文（不含反引号代码区间）不得出现以下任何词：`task_id`, `source_boundary`, `candidate-visible`, `benchmark`, `oracle`, `judge`, `scoring`。注意：反引号包裹的代码标识符不算。 |
| 3.2 | 无实现泄漏 | 不得出现内部模块路径（如 `_internal.utils`）、私有属性名（`_cache`, `__slots__`）。 |

### API 名称覆盖检查

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 3.3 | oracle 测试断言的每个公开类名、方法名、属性名，在 spec 中至少提及一次 | 逐个检查 test_atomic.py 和 test_integration.py 中 assert 涉及的名称。如果一个名字在官方文档里是公开 API，它必须出现在 spec 里。缺一个就是 FAIL。 |
| 3.4 | 不含完整 Python 签名 | spec 中不得出现形如 `ClassName(param: Type = default, ...)` 的完整构造器/方法签名。应改为自然语言行为描述，如"接受一个可选的 config 参数（H2Configuration 类型）"。 |

### Environment 章节检查

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 3.5 | Environment 列出了所有预装包 | 对照 `oracle/{id}/requirements.txt` 每一行，在 Environment 章节中都能找到对应的包名。 |
| 3.6 | Environment 明确声明目标包未预装、无网络 | 必须包含"目标包未预装"和"无网络访问"这两层语义。 |

### Spec 行为覆盖检查

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 3.7 | 每个 oracle 测试函数都能追溯到 spec 中的某段行为描述 | 抽查至少 10 个测试函数，每个都能指出 spec 中的对应段落。如果存在"无法从 spec 推导出应该这样写"的测试，说明 spec 缺失或测试超纲。 |
| 3.8 | Spec 中没有 TBD/TODO 占位符 | 全文搜索 `TBD`, `TODO`, `FIXME`, `XXX`，不得有残留。 |

---

## 四、Oracle 测试质量（14 项）

### 数量与分层

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 4.1 | test_atomic.py ≥ 15 个测试函数 | `ast.parse` 计数以 `test_` 开头的 `FunctionDef`/`AsyncFunctionDef` |
| 4.2 | test_integration.py ≥ 15 个测试函数 | 同上 |
| 4.3 | 总测试函数数 ≥ 50 | atomic + integration + system_e2e ≥ 50 |

### 断言质量

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 4.4 | Atomic 层 positive 断言占比 ≥ 60% | positive = 断言一个产出值（返回值、属性值、输出内容）。failure_path（断言抛异常/错误状态）不算 positive。shape（只查类型/长度不查内容）不算 positive。 |
| 4.5 | Atomic 层无 no_check 测试 | 每个 atomic 测试函数必须至少有一个 assert 语句。 |
| 4.6 | 不断言异常消息原文 | 不得出现 `str(e) == "exact message"`。可以断言异常类型（`isinstance(e, ValueError)`）或包含关键词（`"timeout" in str(e).lower()`）。 |
| 4.7 | 不断言 `__repr__` 格式 | 不得出现 `repr(obj) == "..."` 形式的断言。 |

### 代码健康

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 4.8 | 无重复顶层 import | 同一个名称不得被 import 两次。**实际检查方法**：用 AST 遍历顶层 ImportFrom 节点，收集所有导入的名称，确认无重复。（历史教训：boltons、coveragepy、griffe、nbformat、packaging、prompt_toolkit、quart、vcrpy 都曾犯此错误） |
| 4.9 | 引用的 fixture 文件都存在 | 搜索 `Path(__file__).parent / "xxx"` 形式的引用，确认 `oracle/{id}/xxx` 物理存在。（历史教训：packaging 曾缺失 `pylock/pylock.spec-example.toml`） |
| 4.10 | 不导入目标包的私有模块 | oracle 测试不得 `from target._internal import ...`。只允许导入 spec 中声明的公开 API 表面。 |
| 4.11 | 异步测试有正确配置 | 如果测试使用 `async def test_*`，必须同时满足：(a) `requirements.txt` 包含 `pytest-asyncio`；(b) 存在 `pytest.ini` 或 `conftest.py` 配置 `asyncio_mode = auto`，或每个异步测试函数有 `@pytest.mark.asyncio` 装饰器。（历史教训：quart 曾因缺少 `pytest.ini` 导致异步测试静默跳过） |

### 分层正确性

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 4.12 | Atomic 测试确实是原子的 | 每个 atomic 测试只调用一个函数/方法/构造器，验证其行为。如果一个测试需要先构建复杂状态再调用多个方法协作，它应该在 integration 层。 |
| 4.13 | Integration 测试确实跨组件 | 每个 integration 测试涉及 ≥ 2 个模块/类的交互。只调用一个函数用不同输入的测试不是 integration。 |
| 4.14 | CLI 测试的二进制依赖已满足 | 如果测试通过 `subprocess.run(["tool_name", ...])` 调用 CLI 工具，确认该工具在 `pip install <package>` 后作为 entry_point 可用。不能依赖"PATH 碰巧包含 venv/bin"。（历史教训：copier、dvc 的 CLI 测试都因此失败） |

---

## 五、requirements.txt 完整性（4 项）

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 5.1 | 包含 pytest | 必须有 `pytest` 或 `pytest>=X` |
| 5.2 | 测试代码中 import 的每个第三方包都列出 | 逐行扫描 test_atomic.py 和 test_integration.py 的 import 语句，除了标准库和目标包本身，其余每个包都必须在 requirements.txt 中。（历史教训：requests-cache 缺 `requests-mock`，导致 40 个测试 fixture not found） |
| 5.3 | pytest 插件已列出 | 如果测试使用 `pytest-asyncio`、`pytest-timeout`、`pytest-mock` 等插件功能，必须在 requirements.txt 中列出。 |
| 5.4 | 无多余的目标包自身 | requirements.txt 不得包含目标包本身（那是被测对象，由评分框架安装）。 |

---

## 六、task.json 元数据一致性（8 项）

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 6.1 | `instance_id` == 目录名 | 字符串完全一致 |
| 6.2 | `oracle.count` == 物理测试函数总数 | AST 计数 test_atomic.py + test_integration.py 的 `test_*` 函数数，必须相等 |
| 6.3 | `stats.atomic + stats.integration + stats.system_e2e == oracle.count` | 三层之和等于总数 |
| 6.4 | `taxonomy` 的 key 集合 == 物理测试函数集合 | key 格式为 `test_atomic::func_name` 或 `test_integration::func_name`，必须和物理文件完全一致，不多不少 |
| 6.5 | atomic 文件中的函数 taxonomy 全部 == `"atomic"` | 不允许 atomic 文件里的函数被标为其他层 |
| 6.6 | integration 文件中的函数 taxonomy ∈ {`"integration"`, `"system_e2e"`} | 不允许出现 `"atomic"` 或其他值 |
| 6.7 | `stats` 各层数值 == taxonomy 中该层的计数 | 不能有漂移 |
| 6.8 | 任务出现在 `tasks/metadata.csv` 中 | CSV 中有对应行 |

---

## 七、参考验证（3 项）

**操作方法**：在 Python 3.11 环境中（Docker 或 venv），安装 `requirements.txt` + 参考包，运行 `pytest`。

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 7.1 | 参考包可安装 | `pip install <package>` 成功退出。注意事项：(a) 包名不一定等于 task_id，需确认 PyPI 正确包名；(b) 预发布版本需要 `--pre`；(c) 特定 commit 需要 `pip install git+https://...@commit`。 |
| 7.2 | 全部测试通过 | `pytest oracle/{id}/ -v --tb=short` 结果为 0 failed, 0 error。如果存在**参考版本不具备的功能**（如 bandit 的 SARIF 格式），相关测试必须在 `task.json` 的 `known_reference_skip` 字段中登记，且有明确理由。 |
| 7.3 | Python 版本兼容 | 必须在 Python 3.11（Benchmark Docker 基础镜像版本）下通过。如果包不兼容 3.11，该 task 不可入库。 |

**常见陷阱清单**（历次踩坑总结）：

| 陷阱 | 案例 | 预防措施 |
|------|------|----------|
| PyPI 包名 ≠ task_id | `pre-commit-hooks` 的包名是 `pre-commit` | 检查 `pip show` 确认 |
| 需要 `--pre` | `apscheduler==4.0.0a6` | 检查版本号是否含 a/b/rc |
| 需要 extras | `bandit[baseline]` 提供 `bandit-baseline` 命令 | 检查测试是否调用了 extra 提供的 CLI |
| setuptools_scm 无法从 tarball 安装 | anyio, fsspec | 用 `pip install git+https://` 或 PyPI 发布版 |
| 缺失 pytest 插件 | pytest-timeout, pytest-asyncio | 与 5.3 交叉检查 |
| CLI 不在 PATH | copier, dvc | 确认 venv 的 bin 目录在 PATH 中 |
| Python 版本不兼容 | curio 不兼容 3.12（`mpc.CHALLENGE` 重命名） | 只在 3.11 下验证 |

---

## 八、Dummy 鉴别（2 项）

**操作方法**：创建一个仅含 `__init__.py`（空或仅 `pass`）的空包，安装后运行 oracle 测试。

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 8.1 | 空包通过率 ≤ 10% | 如果空包能通过 > 10% 的测试，说明测试太弱，断言的是"存在性"而非"行为"。 |
| 8.2 | Atomic 和 Integration 都有区分力 | 两层各自的通过率都应 ≤ 15%。如果某一层通过率异常高（如 atomic 30%+），需检查是否有大量 `import X; assert hasattr(X, 'foo')` 式的弱断言。 |

---

## 九、交叉一致性检查（3 项）

以上各部分之间的一致性：

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 9.1 | Spec 的 Installable Surface 章节列出的模块 ⊇ oracle 测试中 import 的目标包模块 | 测试 import 了 `from target.sub import X`，则 spec 必须提及 `target.sub`。 |
| 9.2 | requirements.txt 与 Environment 章节一致 | 两处列出的第三方包集合相同。 |
| 9.3 | task.json 的 `target_imports` 覆盖了测试中实际 import 的目标包顶层模块 | 如测试 import 了 `curio`，则 `target_imports` 必须含 `"curio"`。 |

---

## 检查执行模板

每个 task 的验收记录应如下填写：

```
Task: <task_id>
Date: <yyyy-mm-dd>
Checker: <name>

## 一、文件完整性
- [x] 1.1  spec.md
- [x] 1.2  task.json
- [x] 1.3  test_atomic.py
- [x] 1.4  test_integration.py
- [x] 1.5  requirements.txt

## 二、Spec 结构
- [x] 2.1 ~ 2.11  全部章节存在

## 三、Spec 内容质量
- [x] 3.1  无禁用词
- [x] 3.2  无实现泄漏
- [x] 3.3  API 名称全覆盖
- [x] 3.4  无完整 Python 签名
- [x] 3.5  Environment 列出所有预装包
- [x] 3.6  声明未预装+无网络
- [x] 3.7  测试可追溯到 spec 段落
- [x] 3.8  无 TBD/TODO

## 四、Oracle 测试质量
- [x] 4.1  atomic ≥ 15
- [x] 4.2  integration ≥ 15
- [x] 4.3  total ≥ 50
- [x] 4.4  positive ≥ 60%
- [x] 4.5  无 no_check
- [x] 4.6  不断言异常消息原文
- [x] 4.7  不断言 __repr__
- [x] 4.8  无重复 import
- [x] 4.9  fixture 文件存在
- [x] 4.10 无私有模块导入
- [x] 4.11 异步配置正确
- [x] 4.12 atomic 确实原子
- [x] 4.13 integration 确实跨组件
- [x] 4.14 CLI 依赖满足

## 五、requirements.txt
- [x] 5.1  含 pytest
- [x] 5.2  第三方依赖全列出
- [x] 5.3  pytest 插件已列出
- [x] 5.4  不含目标包

## 六、task.json
- [x] 6.1 ~ 6.8  全部一致

## 七、参考验证
- [x] 7.1  可安装
- [x] 7.2  全通过（或 known_reference_skip 已登记）
- [x] 7.3  Python 3.11 兼容

## 八、Dummy 鉴别
- [x] 8.1  空包通过率 ≤ 10%
- [x] 8.2  各层均有区分力

## 九、交叉一致性
- [x] 9.1  import ⊆ Installable Surface
- [x] 9.2  requirements == Environment
- [x] 9.3  target_imports 覆盖

结论: ✅ ACCEPTED / ❌ REJECTED (reason: ...)
```

---

## 附录：历史故障登记

以下是本项目历次验收中发现的典型故障，作为未来检查的参照：

| 故障 | 涉及 task | 根因 | 对应检查项 |
|------|-----------|------|------------|
| 断言值编造 | bandit | subagent 猜测 issue_text/test_name/CWE 值而非实际运行验证 | 7.2 |
| 缺 requests-mock | requests-cache | requirements.txt 遗漏 fixture 依赖 | 5.2 |
| 缺 pylock.toml | packaging | fixture 文件未从上游获取 | 4.9 |
| 重复 import | 8 个 task | 多轮修改后 import 行未合并 | 4.8 |
| 异步测试静默跳过 | quart | 缺 pytest.ini asyncio_mode | 4.11 |
| Python 3.12 不兼容 | curio | `mpc.CHALLENGE` 重命名 | 7.3 |
| 包名映射错误 | pre-commit-hooks, prompt_toolkit | task_id ≠ PyPI 包名 | 7.1 |
| SARIF 格式不存在 | bandit | 参考版本无此功能 | 7.2 (known_skip) |
| CLI 不在 PATH | copier, dvc | subprocess 调用需要 entry_point | 4.14 |
| positive 断言不足 | dbt-core, apscheduler, vcrpy 等 | atomic 层全是 failure_path | 4.4 |
| Environment 含 "oracle" | 全部 51 题 | 模板化改写引入禁用词 | 3.1 |
| 签名过度规范 | httpx, prompt_toolkit, beancount 等 | spec 含完整 Python 构造器签名 | 3.4 |
