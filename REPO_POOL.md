# Repo Pool — 候选库状态

`../repo-pool/` 下所有库的占用情况。**如果你在为 SpecBench 选候选库，先看这里——已被占用的库不要重复开工。**

---

## 占用中（请勿重复开工）

| 库 | 状态 | 说明 |
|---|---|---|
| `kevin1024__vcrpy` | **QUALIFIED** | vcrpy-fullrepro-001，已在 tasks/ |
| `cookiecutter__cookiecutter` | **QUALIFIED** | cookiecutter-fullrepro-001，已在 tasks/ |
| `simonw__sqlite-utils` | **IN_PROGRESS** | filter v5 canonical，正在减少 primitive cascade |
| `pypa__packaging` | **IN_PROGRESS** | Stage 3 通过，待修正 filter 后重跑 Stage 4 |

## 已退出（本 pipeline 下无法继续）

| 库 | 退出原因 |
|---|---|
| `jrnl-org__jrnl` | module-level 私有 import，clean 环境 collection error |
| `mahmoud__boltons` | 测试覆盖内部工具函数，无法从公开文档派生 spec |
| `mkdocs__mkdocs` | 测试依赖内部 plugin 基础设施 |
| `rochacbruno__dynaconf` | 测试依赖私有 loader 实现细节 |
| `hoechstleistungshaartrockner__xitkit` | docs-test projection mismatch（CLI docs vs Python API tests） |
| `tomlkit` | 大量测试断言内部 repr 格式，behavioral criterion 失败 |

---

## Python — 可选（待评估）

按粗略难度/风险排序，低风险靠前。

| 库 | 功能简介 | 风险提示 |
|---|---|---|
| `lepture__mistune` | 纯 Python Markdown 解析器，插件化渲染器 | — |
| `python-hyper__h11` | sans-I/O HTTP/1.1 状态机实现 | — |
| `TinyDB` | 纯 Python 轻量文档数据库，JSON 后端 | — |
| `pimutils__todoman` | CalDAV todo 管理器，RFC 5545 iCalendar 操作 | — |
| `pre-commit__pre-commit` | git hooks 管理框架，跨语言 hook runner | — |
| `pytest-dev__pytest` | Python 测试框架，fixture/plugin/parametrize 系统 | 体量大，需评估 Stage 3 difficulty |
| `beancount__beancount` | 复式记账 plain-text 会计系统 | ledger 语法可能 spec 难写 |
| `iterative__dvc` | ML 数据版本控制，pipeline + 远程存储 | 外部依赖多，需仔细隔离 |
| `scrapy__scrapy` | 异步 web 爬虫框架，spider + pipeline + middleware | 网络测试需隔离 |
| `snakemake__snakemake` | 生物信息学 workflow 管理，规则依赖图 + 集群调度 | 体量大，外部依赖 |
| `sqlalchemy__alembic` | SQLAlchemy 数据库 schema 迁移工具 | — |
| `sqlalchemy__sqlalchemy` | Python SQL toolkit + ORM，Core + ORM 双层 API | 体量极大，谨慎评估 |
| `pypa__pip` | Python 包安装器，依赖解析 + wheel/sdist 安装 | 体量大，测试套件复杂 |
| `pallets__jinja` | Jinja2 模板引擎 | **高饱和度风险**：强模型可能直接 pattern-match |
| `ansible__ansible` | IT 自动化平台，playbook + inventory + module 系统 | **体量极大**，慎重 |
| `zk-org__zk` | Zettelkasten 笔记工具（Go）| 非 Python，需另行评估 |

---

## 非 Python / 超出范围

pipeline 当前只处理 Python 库。以下库不适合直接用本 pipeline：

| 库 | 语言 |
|---|---|
| `aptly-dev__aptly` | Go |
| `bootandy__dust` | Rust |
| `buchgr__bazel-remote` | Go |
| `chmln__sd` | Rust |
| `confluentinc__schema-registry` | Java |
| `cschleiden__go-workflows` | Go |
| `dstask` | Go |
| `helm__helm` | Go |
| `hostctl` | Go |
| `kopia__kopia` | Go |
| `kyoh86__richgo` | Go |
| `marmite` | Rust |
| `mgdm__htmlq` | Rust |
| `oban-bg__oban` | Elixir |
| `opentofu__opentofu` | Go |
| `redis__redis` | C |
| `restatedev__restate` | Rust / Java |
| `SarthakMakhija__bitcask` | Go |
| `thomaspoignant__go-feature-flag` | Go |
| `todotxt__todo.txt-cli` | Shell |
| `wfxr__csview` | Rust |
