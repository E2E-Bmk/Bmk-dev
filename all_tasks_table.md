# All-tasks master table

Distinct task ids: **197** (Bmk-dev branches ∪ local main ∪ research net-new).

**状态分布**：不合格·judge未过 24 ｜ 不合格·产物不齐 2 ｜ 合格 47 ｜ 合格·待重验 3 ｜ 合格待合入 46 ｜ 待评判 53 ｜ 样本外 22

This table is the shared registry: if a task id appears here it already exists somewhere — do not rebuild it. `in_auth_tree=no` rows live only in a branch or a research dir.

状态枚举（三类失败为终态，另有三类未落地的非失败中间态）：
- `合格` — 已落 main `tasks/<lang>`，全过；`合格·待重验` — 已落 tasks/ 但 note 为 REVALIDATION-REQUIRED/REOPENED_S3。
- `待评判` — 产物在、judge 未跑（ARTIFACT_ONLY / 需重验）；`合格待合入` — judge 过、未 merge 进 main；`样本外` — 齐全能过、不在 aligned-43 本轮样本。
- `不合格·产物不齐`(缺 spec/oracle/task.json) ｜ `不合格·judge未过`(门禁失败：depends_on/taxonomy/ref-candidate 冲突/layer-floor/REJECTED) ｜ `不合格·分数gap不达标`(过 judge 但候选分/gap 不达标；需候选跑分，当前几乎为空)。

- Model score cell = `总分 (a<atomic%>/i<integ%>/g<gap>)`, 总分=(atomic_passed+integ_passed)/(atomic_total+integ_total)。`—`=未跑。`reference(无模型)`=task.json 参考侧通过率。`map=✗`=无映射文件（aligned-43 毕业题映射在 oracle docstring 内）。

| task_id | lang | 来源项目 | 来源分支 | in_auth_tree | spec | tests | map | meta | 状态 | 卡点/说明 | qwen3.8-max | qwen3.8-max-rustfix | deepseek-chat | reference(无模型) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| afero-fs-composition-fullrepro-001 | go | research/spec2repo-multilang | — | no | ✓ | ✓ | ✗ | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| afero-layered-filesystems-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| agate-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| alembic-migrations-fullrepro-001 | ? | Bmk-dev | beta | no | ✓ | ✗ | top-map | ✗ | 不合格·产物不齐 | 无oracle、无task.json | — | — | — | — |
| anyio-async-runtime-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | skipped | ref 100% |
| anytree-tree-structure-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| apischema-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| apscheduler-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| apscheduler-jobs-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| arrow-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 87/87 |
| asciimatics-screen-widget-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| astroid-ast-inference-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| attrs-classes-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| authlib-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| babel-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| bandit-securityscan-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格·待重验 | REVALIDATION-REQUIRED | — | — | — | ref 100% |
| bbolt-transactional-kv-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| beancount-ledger-fullrepro-002 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| boltons-cache-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| boltons-coreutils-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| cargo-generate-fullrepro-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/86 = 0% | — | — | — | — |
| casbin-policy-enforcement-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| cattrs-converters-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| celery-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| cement-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| cerberus-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 84/84 |
| changesets-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| changesets-release-graph-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| chardet-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 90/90 |
| cleo-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 79/79 |
| click-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 82/82 |
| comfy-table-fullrepro-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/69 = 0% | — | — | — | — |
| commons-pool-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| configobj-config-parser-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| cookiecutter-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| copier-template-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| coveragepy-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| cron-utils-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| curio-concurrency-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| curio-task-coordination-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| dateparser-dates-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| dateutil-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 80/80 |
| dbt-core-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 74/74 |
| deal-runtime-contracts-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| deepdiff-object-delta-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| dependency-cruiser-ruleset-fullrepro-001 | typescript | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| depgraph-maven-plugin-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | error | — | — | — |
| diskcache-cache-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| distlib-installed-distribution-projections-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| dnspython-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| dogpile-cache-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| doit-taskrunner-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| doit-taskrunner-fullrepro-002 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格·待重验 | REVALIDATION-REQUIRED | — | — | — | ref 51/51 |
| dramatiq-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| dvc-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| dynaconf-settings-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | oracle/map | ✓ | 合格 |  | — | — | — | — |
| expr-rule-engine-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| ezdxf-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| fastavro-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| flit-pyproject-build-projections-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| fonttools-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| fpdf2-document-layout-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| frictionless-py-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| fsspec-filesystem-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 58/58 |
| gix-config-file-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ROOT-MAP | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/41 = 0% | — | — | — | — |
| gix-ref-txn-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| gix-status-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| glom-data-transform-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| gojq-query-engine-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| goose-sqlite-migrations-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| graphql-inspector-schemadiff-fullrepro-001 | typescript | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| griffe-apimodel-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| gunicorn-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| h2-protocol-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 55/55 |
| halodb-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| hikaricp-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 97/97 |
| httpcore-transport-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| httpx-client-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| httpx-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| huey-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| hy-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 64/64 |
| hypercorn-fullrepro-002 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 52/52 |
| invoke-taskrunner-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| isort-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| japicmp-annotationcompare-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/28 = 0% | — | — | — | — |
| japicmp-annotvalue-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/27 = 0% | — | — | — | — |
| japicmp-binarycompat-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | taxonomy keys do not match the physical test functions | — | — | — | — |
| japicmp-classvalue-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | layer floor failed: atomic=35, integration=23 | — | — | — | — |
| japicmp-ctorannot-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/27 = 0% | — | — | — | — |
| japicmp-fieldannot-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/27 = 0% | — | — | — | — |
| japicmp-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | reference gate and candidate probe disagree, and the conflict is unresolved | — | — | — | — |
| japicmp-genericscompare-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| japicmp-hierarchycompare-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| japicmp-membervalue-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/28 = 0% | — | — | — | — |
| japicmp-methodannot-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/27 = 0% | — | — | — | — |
| japicmp-modelcompare-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| japicmp-specialmods-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/25 = 0% | — | — | — | — |
| jedi-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| jimfs-filesystem-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| jline2-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| jpeek-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| jrnl-journal-fullrepro-002 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| jsonpickle-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 76/76 |
| jsonschema-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 90/90 |
| jupyter-client-kernel-protocol-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| jupytext-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| kedro-pipeline-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| kombu-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| lark-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 711/792 |
| lektor-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| litestar-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| loguru-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| luigi-workflow-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| markdown-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 89/90 |
| markdown-it-py-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 81/81 |
| marshmallow-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| marshmallow-schema-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| mashumaro-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| migrations-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| mkdocs-sitebuild-fullrepro-002 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| mvnresolver-graph-project-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| mvnresolver-graph-transform-001 | java | research/spec2repo | — | no | ✓ | ✗ | ✗ | ✓ | 不合格·产物不齐 | 无oracle | — | — | — | ref 100% |
| mvnresolver-repo-version-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/27 = 0% | — | — | — | — |
| mvnresolver-select-traverse-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| mvnresolver-version-order-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
| nbconvert-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| nbformat-notebook-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| networkx-graph-state-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| nikola-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| nutsdb-transactional-collections-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| oclif-core-cli-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| omegaconf-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| oslo-config-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| packaging-core-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| parso-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 84/84 |
| peewee-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 65/65 |
| pelican-sitegen-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| petl-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pex-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pf4j-fullrepro-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| pgpy-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| pgqueuer-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| pint-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 92/92 |
| poethepoet-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pony-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pre-commit-hooks-fullrepro-002 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| prompt_toolkit-terminal-ui-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| pycparser-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 90/90 |
| pylint-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pymdown-extensions-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pyparsing-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 272/272 |
| pypdf-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 68/68 |
| pypika-sql-builder-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pyserial-loop-url-listports-public-projections | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| python-fire-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| python-semantic-release-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| python-statemachine-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| pyyaml-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| quart-async-web-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| requests-cache-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| rhai-fullrepro-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | taxonomy keys do not match the physical test functions | — | — | — | — |
| ristretto-concurrent-cache-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| rocketry-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| rq-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| sanic-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| schematics-model-validation-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| sqlalchemy-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| sqlalchemy-utils-public-utilities-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| sqlparse-fullrepro-001 | ? | Bmk-dev | LiandZhang | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 59/59 |
| starlette-asgi-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| structlog-event-context-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | — |
| structlog-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| taskchampion-fullrepro-001 | rust | research/spec2repo-multilang | — | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | error | — | ref 100% |
| tengo-script-runtime-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| textual-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| textx-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| tinybase-reactive-store-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| togglz-feature-toggles-fullrepro-001 | java | research/spec2repo-multilang | — | no | ✓ | ✓ | ✗ | ✓ | 待评判 | ARTIFACT_ONLY | 93% (a92%/i93%/g-0.012) | — | — | ref 100% |
| toml-fullrepro-001 | rust | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | taxonomy keys do not match the physical test functions | — | — | — | — |
| toolz-functional-utils-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| tornado-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| tortoise-orm-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| tox-envrunner-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格·待重验 | REOPENED_S3 | — | — | — | — |
| traitlets-core-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| transitions-state-machine-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| typedoc-reflection-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| unstorage-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| validator-struct-rules-fullrepro-001 | go | Bmk-dev | go-tasks-20260821 | no | ✓ | ✓ | top-map | ✓ | 合格待合入 | QUALIFIED | — | — | — | ref 100% |
| vcrpy-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| webob-request-response-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| whoosh-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 合格 |  | — | — | — | — |
| whoosh-index-search-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 样本外 | id is absent from the qualified release sample (spec2repo-aligned-43_PYTHON) | — | — | — | ref 100% |
| wireit-build-graph-fullrepro-001 | typescript | Bmk-dev | li-type | no | ✓ | ✓ | ✗ | ✓ | 合格待合入 | QUALIFIED | — | — | — | — |
| wtforms-form-lifecycle-fullrepro-001 | python | Bmk-dev | main | yes | ✓ | ✓ | top-map | ✓ | 合格 |  | — | — | — | — |
| xlsxwriter-workbook-projections-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| xmlschema-fullrepro-001 | python | Bmk-dev | LiandZhang50-artifact-only | no | ✓ | ✓ | top-map | ✓ | 待评判 | ARTIFACT_ONLY | — | — | — | ref 100% |
| xmlunit-diff-001 | java | Bmk-dev | main | yes | ✓ | ✓ | ✗ | ✓ | 不合格·judge未过 | depends_on coverage below floor: 0/26 = 0% | — | — | — | — |
