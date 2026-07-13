# Spec2Repo Task 审查行动计划

> 审查日期：2026-07-12
> 审查依据：Spec2Repo 立意框架（测量模型在行为规格下自主做出跨模块一致架构决策的能力）
> 核心指标：Integration Gap = Unit Pass Rate − Integration Pass Rate

---

## 一、审查结论概览

| 类别 | 数量 | 说明 |
|------|------|------|
| 通过 | 24 | 符合框架要求，可直接用于 benchmark |
| 需修改 | 8 | 有具体问题必须修复后才能计入有效 benchmark |
| 需补充验证 | 10 | 缺少 reference gate 评分（oracle 未在原始代码上验证 ≥95%）|

---

## 二、问题分类

### A. 饱和/零分辨力（benchmark 无效）

| Task | 问题 | 证据 |
|------|------|------|
| apscheduler-jobs-fullrepro-001 | Candidate 满分 60/60 | MANIFEST 自标 "trivially-solved and saturated-candidate-score" |

### B. Spec 泄漏内部架构（违反"只描述 WHAT 不描述 HOW"）

| Task | 泄漏内容 | 严重程度 |
|------|----------|----------|
| kedro-pipeline-001 | 项目目录结构 `conf/`、`<pkg>.settings` 模块布局 | 很高 |
| boltons-coreutils-001 | Package Layout 节强制 `.py` 文件组织 | 高 |
| mkdocs-sitebuild-002 | ~15 个内部子模块 import 路径 | 高 |
| cookiecutter-001 | 9 个内部子模块 + generate_files 5 步流水线 | 高 |
| pre-commit-hooks-002 | `pre_commit.commands.*` 内部模块树 | 高 |
| starlette-asgi-001 | 中间件栈内部层次 + lazy stack 构建时机 | 中-高 |
| requests-cache-001 | 内部类层次 + 过期优先级算法 | 高 |
| pelican-sitegen-001 | 生成器类继承层次 | 中-高 |
| apscheduler-jobs-001 | 三服务内部架构 + MemoryDataStore 方法 | 高 |
| fsspec-filesystem-001 | `fsspec.implementations.*` 内部路径 | 高 |

### C. 测试设计问题

| Task | 问题 |
|------|------|
| copier-template-001 | 13 个 CLI 测试硬编码 console-script entry module layout（spec 未承诺）|
| packaging-core-001 | 0 个 system_e2e 测试，107 atomic / 16 integration / 0 e2e |
| kedro-pipeline-001 | 仅 5 个 integration 测试（对 pipeline 系统严重不足）|
| vcrpy-fullrepro-001 | 0 个 atomic 测试，无法建立 Unit Pass Rate 基线 |

### D. 缺少 Reference Gate 验证

bandit, starlette, luigi, httpx, dbt-core, pgqueuer, h2-protocol, sqlalchemy, mkdocs-002, nbformat

---

## 三、行动计划（按优先级）

### P0 — 必须在 benchmark 发布前完成

#### P0-1: apscheduler 饱和问题 [DONE]
- **文件**: `tasks/apscheduler-jobs-fullrepro-001/MANIFEST.json`
- **操作**: 将 status 改为 `SATURATED-DISQUALIFIED`，或为 `wip/apscheduler-jobs-fullrepro-001/filter/generated_tests.py` 设计新的高难度集成测试使 candidate 不再满分
- **验收标准**: candidate pass rate < 90%，或明确标注此 task 不计入主分析

#### P0-2: kedro 架构泄漏 + 集成测试不足 [DONE]
- **文件**: `tasks/kedro-pipeline-fullrepro-001/spec.md`
- **操作 A（spec 修复）**: 删除所有 `conf/`、`<package_name>.settings`、`<package_name>.pipeline_registry`、`kedro.framework.project/startup/session` 等内部布局描述，改为从 CLI (`kedro run`) 和 `KedroSession.run()` 的行为角度描述
- **操作 B（测试扩充）**: 在 oracle 中将 integration 测试从 5 个扩充到 20+，覆盖：
  - DataCatalog 共享状态（一个 node 的输出是另一个 node 的输入）
  - Pipeline filter 后的执行顺序正确性
  - Runner 错误传播（上游 node 失败 → 下游不执行）
  - Config 层叠（base + env override）对运行行为的影响
- **验收标准**: integration ≥ 20, taxonomy 重新生成, reference gate ≥ 95%

#### P0-3: boltons 强制文件布局 [DONE]
- **文件**: `tasks/boltons-coreutils-fullrepro-001/spec.md`
- **操作**: 删除 "Package Layout" 节中指定 `boltons/__init__.py`、`cacheutils.py`、`dictutils.py` 等文件名的部分。保留 `from boltons.cacheutils import LRU` 这类公共 import 路径（这是 test-interface contract）
- **附加操作**: 在 MANIFEST.json 的 notes 中添加：`"integration_gap_note": "Modules are fully independent (cacheutils, dictutils, iterutils, urlutils have zero cross-module interaction). Integration Gap is expected to be ~0 for this task; it primarily measures parallel-module implementation capability."`
- **验收标准**: spec 中无文件名/目录组织要求

#### P0-4: copier 测试硬编码 [DONE]
- **文件**: `wip/copier-template-fullrepro-001/filter/generated_tests.py`（或等效 oracle carrier）
- **操作**: 将 13 个使用硬编码 console-script entry module 的 system_e2e CLI 测试重写为：
  - 使用 `subprocess.run(["python", "-m", "copier", ...])` 而非直接调用内部模块
  - 或使用 spec 中承诺的 `run_copy`/`run_recopy`/`run_update` Python API
- **验收标准**: 所有 CLI 测试不依赖任何 spec 未承诺的内部模块路径；reference gate 重新验证 ≥ 95%

---

### P1 — Benchmark 质量提升

#### P1-1: packaging 补充端到端测试 [DONE]
- **文件**: `wip/packaging-core-fullrepro-001/filter/generated_tests.py`
- **操作**: 添加 10+ 个 system_e2e 测试：
  - `Requirement("pkg>=1.0; python_version>='3.8'")` 解析 → `.specifier` 匹配 → `.marker` 评估 → 整体 `Requirement` 满足判定
  - Version ordering + SpecifierSet 交集 + Marker 环境变量组合
- **验收标准**: system_e2e ≥ 10, reference gate ≥ 95%

#### P1-2: mkdocs spec 收敛 [DONE]
- **文件**: `tasks/mkdocs-sitebuild-fullrepro-002/spec.md`
- **操作**: 删除 `mkdocs.structure.files`/`mkdocs.structure.nav`/`mkdocs.structure.pages`/`mkdocs.contrib.search.search_index`/`mkdocs.utils.templates` 等内部路径，保留：
  - CLI: `mkdocs build`, `mkdocs serve`
  - Python API: `load_config()`, `build()`
  - Plugin hook 名称与语义（`on_page_markdown`, `on_env` 等）
- **验收标准**: spec 中不出现非公开 API 的子模块路径

#### P1-3: pre-commit spec 收敛 [DONE]
- **文件**: `tasks/pre-commit-hooks-fullrepro-002/spec.md`
- **操作**: 删除 `pre_commit.commands.*`、`pre_commit.clientlib`、`pre_commit.store`（若为内部实现）、`pre_commit.hook`、`pre_commit.prefix` 等模块路径
- **保留**: `main()` 函数、`load_config()`、CLI 子命令语义、hooks 行为
- **验收标准**: spec 中只保留测试实际需要调用的公开入口

#### P1-4: starlette spec 清理 [DONE]
- **文件**: `tasks/starlette-asgi-fullrepro-001/spec.md`
- **操作**: 删除以下实现细节：
  - 默认中间件栈层次（"ServerErrorMiddleware 最外、ExceptionMiddleware 最内"）
  - lazy middleware stack 构建时机描述
  - 将 15+ 条 `from starlette.xxx import Yyy` 按是否为公开文档化 API 筛选，非公开的删除
- **验收标准**: spec 只描述中间件的可观测行为（"未处理异常返回 500"），不规定实现层次

#### P1-5: vcrpy 补充 atomic 测试 [DONE]
- **文件**: `wip/vcrpy-fullrepro-001/filter/generated_tests.py` + `taxonomy.jsonl`
- **操作**: 添加 5-10 个 atomic 层测试：
  - Request/Response 对象构造与属性
  - Matcher 单独匹配逻辑（URI matcher、header matcher）
  - Cassette 序列化/反序列化单元
- **验收标准**: atomic ≥ 5, taxonomy 更新, reference gate 保持 ≥ 95%

#### P1-6: cookiecutter spec 收敛 [DONE]
- **文件**: `tasks/cookiecutter-fullrepro-001/spec.md`
- **操作**: 将 "Public Modules" 节删除或收敛为：
  - 顶层 API: `cookiecutter.main.cookiecutter()` + CLI `cookiecutter <template>`
  - 删除 `generate_files` 5 步流水线描述
  - 删除 `StrictEnvironment`、`YesNoPrompt`、`JsonPrompt` 等内部类名
- **验收标准**: spec 中不出现内部模块名/流水线步骤编号

#### P1-7: requests-cache spec 清理 [DONE]
- **文件**: `tasks/requests-cache-fullrepro-001/spec.md`
- **操作**: 
  - 删除内部类：`SerializerPipeline`、`Stage`、`SQLiteDict`、`LRUFileDict`
  - 删除过期优先级 1-5 编号算法（改为"优先使用请求级设置，其次 session 级"的行为描述）
  - 保留：`CachedSession` 行为、backend 别名、patcher、Cross-View Invariants
- **验收标准**: spec 中无内部类层次描述，无算法编号

---

### P2 — 完善性工作

#### P2-1: Reference Gate 批量验证 [DONE]
- **涉及 task**: bandit, starlette, luigi, httpx, dbt-core, pgqueuer, h2-protocol, sqlalchemy, mkdocs-002, nbformat
- **操作**: 对每个 task，在 WSL 环境中：
  1. 使用 `harness/score_pytest_original.py` + 对应 `--remove-path` 参数
  2. 以 `repo-pool/` 中的原始代码作为 solution
  3. 运行 `kept_nodeids.txt` 中的全部测试
  4. 验证 pass rate ≥ 95%
  5. 生成 `reference_score.json` 并放入 `tasks/{task-id}/`
- **验收标准**: 每个 task 有 reference_score.json，pass rate ≥ 95%

#### P2-2: apscheduler spec 架构泄漏清理 [DONE]
- **文件**: `tasks/apscheduler-jobs-fullrepro-001/spec.md`
- **操作**: 删除三服务架构描述、`apscheduler.datastores.memory`/`apscheduler.eventbrokers.local`/`apscheduler.executors.*` 内部路径、MemoryDataStore 内部方法规格
- **验收标准**: spec 从公开 Scheduler/AsyncScheduler API 角度描述行为

#### P2-3: pelican spec 清理 [DONE]
- **文件**: `tasks/pelican-sitegen-fullrepro-001/spec.md`
- **操作**: 将 `Generator → ArticlesGenerator/PagesGenerator/StaticGenerator` 继承层次描述改为行为描述（"系统能生成文章页、独立页、静态文件"）
- **验收标准**: spec 不强制特定类继承结构

#### P2-4: fsspec spec 清理 [DONE]
- **文件**: `tasks/fsspec-filesystem-fullrepro-001/spec.md`
- **操作**: 删除 `fsspec.implementations.memory`、`fsspec.implementations.local` 等内部模块路径，保留 `filesystem("memory")` 等公开入口
- **验收标准**: spec 不出现 `implementations` 子包路径

#### P2-5: 标注低分辨力 task [DONE]
- **涉及**: diskcache-cache-001, dateparser-dates-001
- **操作**: 在各自 MANIFEST.json 的 notes 中添加：
  - diskcache: `"discrimination_note": "Candidate 95.5% pass rate, near-saturated. Integration Gap signal may be weak."`
  - dateparser: `"discrimination_note": "76% atomic tests; Integration Gap signal expected to be weak due to low cross-module interaction."`
- **验收标准**: MANIFEST 中有明确标注

---

## 四、通过的 Task 列表（无需修改）

以下 task 符合 Spec2Repo 框架，可直接纳入 benchmark：

1. doit-taskrunner-fullrepro-002
2. cattrs-converters-fullrepro-001
3. httpcore-transport-fullrepro-001
4. marshmallow-schema-fullrepro-001
5. attrs-classes-fullrepro-001
6. fsspec-filesystem-fullrepro-001（spec 需 P2 清理，但不影响有效性）
7. requests-cache-fullrepro-001（spec 需 P1 清理，但不影响有效性）
8. dynaconf-settings-fullrepro-001
9. pelican-sitegen-fullrepro-001（spec 需 P2 清理）
10. invoke-taskrunner-fullrepro-001
11. pre-commit-hooks-fullrepro-002（spec 需 P1 清理）
12. beancount-ledger-fullrepro-002
13. coveragepy-fullrepro-001
14. tox-envrunner-fullrepro-001
15. dvc-fullrepro-001
16. httpx-client-fullrepro-001
17. dbt-core-fullrepro-001
18. pgqueuer-fullrepro-001
19. h2-protocol-fullrepro-001
20. sqlalchemy-fullrepro-001
21. luigi-workflow-fullrepro-001
22. bandit-securityscan-fullrepro-001
23. nbformat-notebook-fullrepro-001
24. dateparser-dates-fullrepro-001（附带低分辨力标注）

---

## 五、补充说明

### 关于 Spec 字数
Spec 字数（当前中位数 ~3000 词）不是问题。关键是信息种类：
- ✅ 行为约束、跨模块不变量、test-interface contract → 越多越好（产生更大 Integration Gap 空间）
- ❌ 内部文件组织、算法选择、类层次 → 必须删除

### 关于 "公共 API 路径" vs "内部架构"
`from starlette.routing import Route` 属于公共 API（test-interface contract），不算泄漏。
`from starlette.middleware.errors import ServerErrorMiddleware` + "它必须是最外层" = 泄漏实现。

区分标准：如果删掉这条信息，模型是否仍能通过测试？
- 能通过 → 这条是冗余的实现暗示，删除
- 不能通过 → 这是必要的 test-interface contract，保留
