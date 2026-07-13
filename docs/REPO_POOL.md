# Repo Pool — 候选库状态

`../repo-pool/` 下所有库的占用情况。**如果你在为 SpecBench 选候选库，先看这里——所有库均已被本项目占用，请勿重复开工。**

---

## 占用中

所有 Python 库均已纳入本项目 pipeline，按当前进度分档如下：

### QUALIFIED（已出任务）

| 库 | 任务 ID |
|---|---|
| `kevin1024__vcrpy` | vcrpy-fullrepro-001（在 tasks/） |
| `cookiecutter__cookiecutter` | cookiecutter-fullrepro-001（在 tasks/） |

### IN_PROGRESS（流水线进行中）

| 库 | 当前阶段 |
|---|---|
| `simonw__sqlite-utils` | filter v5 canonical，正在减少 primitive cascade |
| `pypa__packaging` | Stage 3 通过，待修正 filter 后重跑 Stage 4 |

### PENDING（待流水线）

| 库 | 功能简介 |
|---|---|
| `ansible__ansible` | IT 自动化平台，playbook + inventory + module 系统 |
| `beancount__beancount` | 复式记账 plain-text 会计系统 |
| `iterative__dvc` | ML 数据版本控制，pipeline + 远程存储 |
| `lepture__mistune` | 纯 Python Markdown 解析器，插件化渲染器 |
| `pallets__jinja` | Jinja2 模板引擎 |
| `pimutils__todoman` | CalDAV todo 管理器，RFC 5545 iCalendar 操作 |
| `pre-commit__pre-commit` | git hooks 管理框架，跨语言 hook runner |
| `pypa__pip` | Python 包安装器，依赖解析 + wheel/sdist 安装 |
| `pytest-dev__pytest` | Python 测试框架，fixture/plugin/parametrize 系统 |
| `python-hyper__h11` | sans-I/O HTTP/1.1 状态机实现 |
| `scrapy__scrapy` | 异步 web 爬虫框架，spider + pipeline + middleware |
| `snakemake__snakemake` | 生物信息学 workflow 管理，规则依赖图 + 集群调度 |
| `sqlalchemy__alembic` | SQLAlchemy 数据库 schema 迁移工具 |
| `sqlalchemy__sqlalchemy` | Python SQL toolkit + ORM，Core + ORM 双层 API |
| `TinyDB` | 纯 Python 轻量文档数据库，JSON 后端 |
| `zk-org__zk` | Zettelkasten 笔记工具 |

---

## 已退出（本 pipeline 下不可继续）

| 库 | 退出原因 |
|---|---|
| `jrnl-org__jrnl` | module-level 私有 import，clean 环境 collection error |
| `mahmoud__boltons` | 测试覆盖内部工具函数，无法从公开文档派生 spec |
| `mkdocs__mkdocs` | 测试依赖内部 plugin 基础设施 |
| `rochacbruno__dynaconf` | 测试依赖私有 loader 实现细节 |
| `hoechstleistungshaartrockner__xitkit` | docs-test projection mismatch（CLI docs vs Python API tests） |
| `tomlkit` | 大量测试断言内部 repr 格式，behavioral criterion 失败 |

---

## 非 Python / 超出范围

pipeline 当前只处理 Python 库。

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
