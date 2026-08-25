# Repo Status

> 最后更新：2026-08-05
> 用途：组员认领 task 前查阅，避免重复工作
> 本表由 `tasks/` 下的实际文件生成，不手工维护。重新生成见文末命令。

---

## tasks/ 中的 task（60 个）

> 表头说明：`Lang` 取 `task.json` 的 `language` 字段，评分沙箱据此选择测试运行器。
> `Atomic`/`Integ` 是 oracle 文件里实际的测试函数数（`ast` 计数，非 `task.json` 自述）。
> `Lint` 是 `harness/core/oracle_import_lint.py` 的结果 —— 它检查 oracle 是否断言了 spec
> 从未声明的符号。`Static` 是 `harness/core/verify_task.py` 的结果：章节完整性、层底线、
> 断言构成、metadata 与物理文件一致性、`depends_on` 覆盖率、fixture 完整性。
> `Status` 取 `task.json`，是流水线状态而非静态校验结论 —— 两者互相独立。

| # | Task ID | 上游 Repo | Lang | Status | Atomic | Integ | Total | Lint | Static |
|---|---------|-----------|------|--------|--------|-------|-------|------|--------|
| 1 | anyio-async-runtime-fullrepro-001 | agronholm/anyio | python | QUALIFIED | 56 | 28 | 84 | PASS | PASS |
| 2 | apscheduler-jobs-fullrepro-001 | agronholm/apscheduler | python | REVALIDATION-REQUIRED | 41 | 42 | 83 | PASS | PASS |
| 3 | astroid-ast-inference-fullrepro-001 | pylint-dev/astroid | python | QUALIFIED | 51 | 29 | 80 | PASS | PASS |
| 4 | attrs-classes-fullrepro-001 | python-attrs/attrs | python | REVALIDATION-REQUIRED | 50 | 35 | 85 | PASS | PASS |
| 5 | authlib-fullrepro-001 | lepture/authlib | python | QUALIFIED | 39 | 29 | 68 | PASS | WARN |
| 6 | babel-fullrepro-001 | python-babel/babel | python | QUALIFIED | 55 | 37 | 92 | PASS | FAIL |
| 7 | bandit-securityscan-fullrepro-001 | PyCQA/bandit | python | REVALIDATION-REQUIRED | 30 | 37 | 67 | PASS | PASS |
| 8 | beancount-ledger-fullrepro-002 | beancount/beancount | python | REVALIDATION-REQUIRED | 30 | 31 | 61 | PASS | PASS |
| 9 | boltons-coreutils-fullrepro-001 | mahmoud/boltons | python | REVALIDATION-REQUIRED | 137 | 31 | 168 | PASS | PASS |
| 10 | cattrs-converters-fullrepro-001 | python-attrs/cattrs | python | REVALIDATION-REQUIRED | 46 | 26 | 72 | PASS | PASS |
| 11 | cookiecutter-fullrepro-001 | cookiecutter/cookiecutter | python | REVALIDATION-REQUIRED | 36 | 65 | 101 | PASS | PASS |
| 12 | copier-template-fullrepro-001 | copier-org/copier | python | REVALIDATION-REQUIRED | 31 | 29 | 60 | PASS | PASS |
| 13 | coveragepy-fullrepro-001 | nedbat/coveragepy | python | REVALIDATION-REQUIRED | 30 | 30 | 60 | PASS | PASS |
| 14 | curio-task-coordination-fullrepro-001 | dabeaz/curio | python | QUALIFIED | 35 | 36 | 71 | PASS | PASS |
| 15 | dateparser-dates-fullrepro-001 | scrapinghub/dateparser | python | REVALIDATION-REQUIRED | 60 | 29 | 89 | PASS | PASS |
| 16 | dbt-core-fullrepro-001 | dbt-labs/dbt-core | python | REVALIDATION-REQUIRED | 36 | 26 | 62 | PASS | PASS |
| 17 | deal-runtime-contracts-fullrepro-001 | deal | python | QUALIFIED | 31 | 32 | 63 | PASS | PASS |
| 18 | diskcache-cache-fullrepro-001 | grantjenks/python-diskcache | python | REVALIDATION-REQUIRED | 48 | 34 | 82 | PASS | PASS |
| 19 | dnspython-fullrepro-001 | rthalley/dnspython | python | QUALIFIED | 52 | 30 | 82 | FAIL | FAIL |
| 20 | doit-taskrunner-fullrepro-002 | pydoit/doit | python | REVALIDATION-REQUIRED | 36 | 35 | 71 | PASS | PASS |
| 21 | dvc-fullrepro-001 | iterative/dvc | python | REVALIDATION-REQUIRED | 33 | 38 | 71 | PASS | PASS |
| 22 | dynaconf-settings-fullrepro-001 | rochacbruno/dynaconf | python | REVALIDATION-REQUIRED | 30 | 43 | 73 | PASS | PASS |
| 23 | fsspec-filesystem-fullrepro-001 | fsspec/filesystem_spec | python | REVALIDATION-REQUIRED | 36 | 35 | 71 | PASS | PASS |
| 24 | griffe-apimodel-fullrepro-001 | mkdocstrings/griffe | python | REVALIDATION-REQUIRED | 30 | 30 | 60 | PASS | PASS |
| 25 | h2-protocol-fullrepro-001 | python-hyper/h2 | python | REVALIDATION-REQUIRED | 39 | 39 | 78 | PASS | PASS |
| 26 | httpcore-transport-fullrepro-001 | encode/httpcore | python | REOPENED_S3 | 31 | 47 | 78 | PASS | PASS |
| 27 | httpx-client-fullrepro-001 | encode/httpx | python | REOPENED_S3 | 40 | 31 | 71 | PASS | PASS |
| 28 | invoke-taskrunner-fullrepro-001 | pyinvoke/invoke | python | REOPENED_S3 | 47 | 37 | 84 | PASS | PASS |
| 29 | jrnl-journal-fullrepro-002 | jrnl-org/jrnl | python | REOPENED_S3 | 64 | 58 | 122 | PASS | PASS |
| 30 | jupyter-client-kernel-protocol-fullrepro-001 | jupyter_client | python | QUALIFIED | 30 | 30 | 60 | PASS | PASS |
| 31 | kedro-pipeline-fullrepro-001 | kedro-org/kedro | python | REOPENED_S3 | 62 | 33 | 95 | PASS | PASS |
| 32 | loguru-fullrepro-001 | Delgan/loguru | python | STATICALLY_VALIDATED | 66 | 58 | 124 | PASS | PASS |
| 33 | luigi-workflow-fullrepro-001 | spotify/luigi | python | REOPENED_S3 | 40 | 25 | 65 | PASS | PASS |
| 34 | marshmallow-schema-fullrepro-001 | marshmallow-code/marshmallow | python | REOPENED_S3 | 49 | 39 | 88 | PASS | PASS |
| 35 | mkdocs-sitebuild-fullrepro-002 | mkdocs/mkdocs | python | REOPENED_S3 | 69 | 27 | 96 | PASS | PASS |
| 36 | nbformat-notebook-fullrepro-001 | jupyter/nbformat | python | REOPENED_S3 | 42 | 26 | 68 | PASS | PASS |
| 37 | networkx-graph-state-fullrepro-001 | networkx/networkx | python | QUALIFIED | 55 | 32 | 87 | PASS | PASS |
| 38 | nikola-fullrepro-001 | getnikola/nikola | python | QUALIFIED | 40 | 26 | 66 | PASS | WARN |
| 39 | packaging-core-fullrepro-001 | pypa/packaging | python | REVALIDATION-REQUIRED | 55 | 39 | 94 | PASS | PASS |
| 40 | peewee-fullrepro-001 | coleifer/peewee | python | QUALIFIED | 30 | 35 | 65 | PASS | PASS |
| 41 | pelican-sitegen-fullrepro-001 | getpelican/pelican | python | QUALIFIED | 41 | 28 | 69 | PASS | PASS |
| 42 | pgqueuer-fullrepro-001 | janbjorge/pgqueuer | python | QUALIFIED | 30 | 35 | 65 | PASS | PASS |
| 43 | pint-fullrepro-001 | hgrecco/pint | python | QUALIFIED | 56 | 36 | 92 | PASS | FAIL |
| 44 | pre-commit-hooks-fullrepro-002 | pre-commit/pre-commit | python | REOPENED_S3 | 59 | 44 | 103 | PASS | PASS |
| 45 | prompt_toolkit-terminal-ui-fullrepro-001 | prompt-toolkit/python-prompt-toolkit | python | QUALIFIED | 79 | 25 | 104 | PASS | PASS |
| 46 | pypdf-fullrepro-001 | py-pdf/pypdf | python | QUALIFIED | 36 | 32 | 68 | PASS | PASS |
| 47 | quart-async-web-fullrepro-001 | pallets/quart | python | QUALIFIED | 30 | 34 | 64 | PASS | PASS |
| 48 | requests-cache-fullrepro-001 | requests-cache/requests-cache | python | REVALIDATION-REQUIRED | 31 | 31 | 62 | PASS | PASS |
| 49 | rq-fullrepro-001 | rq/rq | python | QUALIFIED | 31 | 36 | 67 | FAIL | FAIL |
| 50 | schematics-model-validation-fullrepro-001 | schematics | python | QUALIFIED | 40 | 28 | 68 | PASS | PASS |
| 51 | sqlalchemy-fullrepro-001 | sqlalchemy/sqlalchemy | python | REVALIDATION-REQUIRED | 30 | 39 | 69 | PASS | PASS |
| 52 | starlette-asgi-fullrepro-001 | encode/starlette | python | QUALIFIED | 30 | 33 | 63 | PASS | PASS |
| 53 | structlog-event-context-fullrepro-001 | hynek/structlog | python | QUALIFIED | 30 | 30 | 60 | PASS | PASS |
| 54 | tox-envrunner-fullrepro-001 | tox-dev/tox | python | REOPENED_S3 | 34 | 26 | 60 | PASS | PASS |
| 55 | traitlets-core-fullrepro-001 | ipython/traitlets | python | QUALIFIED | 31 | 41 | 72 | PASS | PASS |
| 56 | transitions-state-machine-fullrepro-001 | pytransitions/transitions | python | QUALIFIED | 68 | 29 | 97 | PASS | PASS |
| 57 | vcrpy-fullrepro-001 | kevin1024/vcrpy | python | REOPENED_S3 | 41 | 31 | 72 | PASS | PASS |
| 58 | webob-request-response-fullrepro-001 | Pylons/webob | python | QUALIFIED | 49 | 25 | 74 | PASS | PASS |
| 59 | whoosh-index-search-fullrepro-001 | mchaput/whoosh | python | QUALIFIED | 35 | 49 | 84 | PASS | PASS |
| 60 | wtforms-form-lifecycle-fullrepro-001 | pallets-eco/wtforms | python | QUALIFIED | 32 | 28 | 60 | PASS | PASS |

**统计**：Atomic 总计 2631，Integration 总计 2059，总测试 4690。达到 A≥30 / I≥25 / T≥60 的：60/60。

**Status 分布**：QUALIFIED 26，REVALIDATION-REQUIRED 21，REOPENED_S3 12，STATICALLY_VALIDATED 1。

**校验**：Lint PASS 58/60，Static PASS+WARN 56/60。

### 未通过静态校验的 task

| Task ID | 问题 |
|---------|------|
| babel-fullrepro-001 | `depends_on` 引用 4 个不存在的 atomic 测试 |
| dnspython-fullrepro-001 | `depends_on` 引用 7 个不存在的 atomic 测试；oracle 断言 17 个 spec 未声明的符号 |
| pint-fullrepro-001 | `depends_on` 引用 4 个不存在的 atomic 测试（其中若干指向 integration 文件内的函数，含自我依赖）|
| rq-fullrepro-001 | oracle 从 `rq.exceptions` 导入，spec 的 Import Surface 未声明该路径（三个异常类名本身在正文出现）|

这四个都是 SDD 重写之后新建或未随之更新的 task。`depends_on` 指向不存在的测试会让
True Integration Gap 无法计算；未声明符号是 httpcore 事故的形状（照 spec 实现的交付无法
满足这类断言，而复刻上游内部结构的交付可以）。修这两类需要改 oracle 与 spec 内容，属
test-filter 与 spec-writer 的职责，不在台账维护范围内。

---

## 进行中（wip/ 中）

`wip/{language}/{task}/` 是构建过程的工作区，不进版本库（见 `.gitignore`），所以 clone 出来看不到
它。`kept_nodeids.txt`、`taxonomy.jsonl`、`spec_test_map.md` 留在那里作为过滤的审计追踪，
毕业时不复制进 `tasks/{language}/{id}/`。认领任务前先跟负责人确认在建 task，本表只反映已毕业的。

---

## 质量标准

- Spec 标准：`Spec2Repo/docs/SPEC_STANDARD.md`（6 层结构）
- Oracle 标准：`docs/ORACLE_STANDARD.md`（A≥30, I≥25, T≥60, depends_on≥50%）
- 静态门禁：`docs/QUALITY_GATE.md`，由 `harness/core/verify_task.py` 实施
- 验收清单：`docs/ACCEPTANCE_CHECKLIST.md`

## 重新生成本表

```bash
python harness/core/validate_ledger.py            # 全部 task 的静态校验 + 台账交叉检查
python harness/core/sync_task_metadata.py --all --check   # 检查 task.json 是否与 oracle 文件漂移
```
