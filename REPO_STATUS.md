# Repo Status

> 最后更新：2026-08-03
> 用途：组员认领 task 前查阅，避免重复工作

---

## 已完成（tasks/ 中，56 个）

> 表头说明：`Lang` 取 `task.json` 的 `language` 字段（`python` / `go` /
> `typescript` / `rust` / `java`），评分沙箱据此选择测试运行器；`Ref` 记录参考
> 实现是否在完整 oracle 上零失败，它是判定"低分是能力问题还是 oracle 缺陷"的
> 硬判据；`Lint` 记录 `harness/oracle_import_lint.py` 是否输出 `LINT_PASS`。
> 三列留空表示尚未核验，不表示通过。

| # | Task ID | 上游 Repo | Lang | Atomic | Integ | Total | Ref | Lint |
|---|---------|-----------|------|--------|-------|-------|-----|------|
| 1 | anyio-async-runtime-fullrepro-001 | agronholm/anyio | python | 56 | 28 | 84 |  |  |
| 2 | apscheduler-jobs-fullrepro-001 | agronholm/apscheduler | python | 41 | 42 | 83 |  |  |
| 3 | astroid-ast-inference-fullrepro-001 | pylint-dev/astroid | python | 51 | 29 | 80 |  |  |
| 4 | attrs-classes-fullrepro-001 | python-attrs/attrs | python | 50 | 35 | 85 |  |  |
| 5 | authlib-fullrepro-001 | lepture/authlib | python | 39 | 29 | 68 |  |  |
| 6 | bandit-securityscan-fullrepro-001 | PyCQA/bandit | python | 30 | 37 | 67 |  |  |
| 7 | beancount-ledger-fullrepro-002 | beancount/beancount | python | 30 | 31 | 61 |  |  |
| 8 | boltons-coreutils-fullrepro-001 | mahmoud/boltons | python | 137 | 31 | 168 |  |  |
| 9 | cattrs-converters-fullrepro-001 | python-attrs/cattrs | python | 46 | 26 | 72 |  |  |
| 10 | cookiecutter-fullrepro-001 | cookiecutter/cookiecutter | python | 36 | 65 | 101 |  |  |
| 11 | copier-template-fullrepro-001 | copier-org/copier | python | 31 | 29 | 60 |  |  |
| 12 | coveragepy-fullrepro-001 | nedbat/coveragepy | python | 30 | 30 | 60 |  |  |
| 13 | curio-task-coordination-fullrepro-001 | dabeaz/curio | python | 35 | 36 | 71 |  |  |
| 14 | dateparser-dates-fullrepro-001 | scrapinghub/dateparser | python | 60 | 29 | 89 |  |  |
| 15 | dbt-core-fullrepro-001 | dbt-labs/dbt-core | python | 36 | 26 | 62 |  |  |
| 16 | deal-runtime-contracts-fullrepro-001 | life4/deal | python | 31 | 32 | 63 |  |  |
| 17 | diskcache-cache-fullrepro-001 | grantjenks/python-diskcache | python | 48 | 34 | 82 |  |  |
| 18 | doit-taskrunner-fullrepro-002 | pydoit/doit | python | 36 | 35 | 71 |  |  |
| 19 | dvc-fullrepro-001 | iterative/dvc | python | 33 | 38 | 71 |  |  |
| 20 | dynaconf-settings-fullrepro-001 | rochacbruno/dynaconf | python | 30 | 43 | 73 |  |  |
| 21 | fsspec-filesystem-fullrepro-001 | fsspec/filesystem_spec | python | 36 | 35 | 71 |  |  |
| 22 | griffe-apimodel-fullrepro-001 | mkdocstrings/griffe | python | 30 | 30 | 60 |  |  |
| 23 | h2-protocol-fullrepro-001 | python-hyper/h2 | python | 39 | 39 | 78 |  |  |
| 24 | httpcore-transport-fullrepro-001 | encode/httpcore | python | 38 | 47 | 85 |  |  |
| 25 | httpx-client-fullrepro-001 | encode/httpx | python | 40 | 31 | 71 |  |  |
| 26 | invoke-taskrunner-fullrepro-001 | pyinvoke/invoke | python | 47 | 37 | 84 |  |  |
| 27 | jrnl-journal-fullrepro-002 | jrnl-org/jrnl | python | 64 | 58 | 122 |  |  |
| 28 | jupyter-client-kernel-protocol-fullrepro-001 | jupyter/jupyter_client | python | 30 | 30 | 60 |  |  |
| 29 | kedro-pipeline-fullrepro-001 | kedro-org/kedro | python | 62 | 33 | 95 |  |  |
| 30 | loguru-fullrepro-001 | Delgan/loguru | python | 66 | 58 | 124 |  |  |
| 31 | luigi-workflow-fullrepro-001 | spotify/luigi | python | 40 | 25 | 65 |  |  |
| 32 | marshmallow-schema-fullrepro-001 | marshmallow-code/marshmallow | python | 49 | 39 | 88 |  |  |
| 33 | mkdocs-sitebuild-fullrepro-002 | mkdocs/mkdocs | python | 69 | 27 | 96 |  |  |
| 34 | nbformat-notebook-fullrepro-001 | jupyter/nbformat | python | 42 | 26 | 68 |  |  |
| 35 | networkx-graph-state-fullrepro-001 | networkx/networkx | python | 55 | 32 | 87 |  |  |
| 36 | nikola-fullrepro-001 | getnikola/nikola | python | 40 | 26 | 66 |  |  |
| 37 | packaging-core-fullrepro-001 | pypa/packaging | python | 55 | 39 | 94 |  |  |
| 38 | pelican-sitegen-fullrepro-001 | getpelican/pelican | python | 41 | 28 | 69 |  |  |
| 39 | pgqueuer-fullrepro-001 | janbjorge/pgqueuer | python | 30 | 35 | 65 |  |  |
| 40 | pre-commit-hooks-fullrepro-002 | pre-commit/pre-commit | python | 59 | 44 | 103 |  |  |
| 41 | prompt_toolkit-terminal-ui-fullrepro-001 | prompt-toolkit/python-prompt-toolkit | python | 79 | 25 | 104 |  |  |
| 42 | quart-async-web-fullrepro-001 | pallets/quart | python | 30 | 34 | 64 |  |  |
| 43 | requests-cache-fullrepro-001 | requests-cache/requests-cache | python | 31 | 31 | 62 |  |  |
| 44 | rq-fullrepro-001 | rq/rq | python | 31 | 36 | 67 |  |  |
| 45 | schematics-model-validation-fullrepro-001 | schematics/schematics | python | 40 | 28 | 68 |  |  |
| 46 | sqlalchemy-fullrepro-001 | sqlalchemy/sqlalchemy | python | 30 | 39 | 69 |  |  |
| 47 | starlette-asgi-fullrepro-001 | encode/starlette | python | 30 | 33 | 63 |  |  |
| 48 | structlog-event-context-fullrepro-001 | hynek/structlog | python | 30 | 30 | 60 |  |  |
| 49 | tox-envrunner-fullrepro-001 | tox-dev/tox | python | 34 | 26 | 60 |  |  |
| 50 | traitlets-core-fullrepro-001 | ipython/traitlets | python | 31 | 41 | 72 |  |  |
| 51 | transitions-state-machine-fullrepro-001 | pytransitions/transitions | python | 68 | 29 | 97 |  |  |
| 52 | vcrpy-fullrepro-001 | kevin1024/vcrpy | python | 41 | 31 | 72 |  |  |
| 53 | webob-request-response-fullrepro-001 | Pylons/webob | python | 49 | 25 | 74 |  |  |
| 54 | whoosh-index-search-fullrepro-001 | mchaput/whoosh | python | 35 | 49 | 84 |  |  |
| 55 | wtforms-form-lifecycle-fullrepro-001 | pallets-eco/wtforms | python | 32 | 28 | 60 |  |  |
| 56 | pypdf-fullrepro-001 | py-pdf/pypdf | python | 36 | 32 | 68 |  |  |

**统计**：Atomic 总计 2399，Integration 总计 1900，总测试 4299。全部达标 A≥30, I≥25, T≥60。

---

## 进行中（wip/ 中）

| Task ID | 上游 Repo | 阶段 |
|---------|-----------|------|
| peewee-fullrepro-001 | coleifer/peewee | S1 已选中 |
| typer-fullrepro-001 | fastapi/typer | 已退休 |


---

## 质量标准

- Spec 标准：`docs/SPEC_STANDARD.md`
- Oracle 标准：`docs/ORACLE_STANDARD.md`（要求 A≥30, I≥25, T≥60, depends_on≥50%）
- 验收清单：`docs/ACCEPTANCE_CHECKLIST.md`
