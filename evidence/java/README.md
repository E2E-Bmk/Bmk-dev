# Java 评测证据

## 来源

本目录的文件迁自临时构造工作区 `javabench` 的 `eval/runs/` 与 `wip/`，该工作区不保留。文件按原样复制，未作改写。目录只是索引与判读说明，不复述构造过程。

## 目录结构

- `measurements/<run>/<task_id>/result.json` —— 39 份评分产物，每份对应一次 scorer 运行。
- `construction/<task_id>/PIPELINE_STATE.md` —— 10 份流水线状态记录，标明该题当时停在哪一阶段。
- `construction/<task_id>/spec_v1.md` —— 3 份带 `INTERNAL` 注释头的初版规格。头部登记了变异族（mutation family，即规格中被有意改写、使实现不能照抄上游的行为点）。

## 三类 run

`<run>` 目录名沿用当时的临时命名，无统一规范，按前缀区分：

- `*-reference` 与 `reference`，共 8 个 —— 参考实现门禁，用于验证 scorer 能把参考实现复现到 100%。8 次全部 `atomic` 与 `integ` 双 100%、`adjusted_gap` 为 0。
- `qwen-*` 共 20 个、`qwen2-*` 共 10 个 —— 候选模型采样，先后两轮。第一轮 20 次里 14 次为 `error`，第二轮 10 次里 1 次为 `error`。
- `sigfix-*`，1 个 —— 签名修复后的对照运行，结果仍为 `error`。

## `result.json` 字段读法

顶层四键：`task_id`、`language`、`agent`、`score`。`agent.status` 有两种取值：27 次为 `ok`（候选实际运行过），12 次为 `skipped (score-only)`（只跑评分）。判读集中在 `score`：

- `status` —— 仅 `ok` 时读数可用。`error` 时 `atomic_total` 与 `integ_total` 多为 0，表示测试根本未被收集，不可当作 0 分。
- `atomic_passed` / `atomic_total`、`integ_passed` / `integ_total` —— 原子测试与集成测试的通过数与总数。
- `adjusted_gap` —— 两类通过率之差，是题目区分度的直接读数；`status` 为 `error` 时是 `null`。
- `gap_confidence`、`elapsed`、`batches` —— 置信度、耗时、分批执行记录。
- `provenance` —— 以 `__PROVENANCE__` 前缀承载的 JSON，记目标依赖的解析结果，用于确认候选改写的是目标库本身，而非引用了预编译产物。
- `tests` —— 逐个测试的 `passed` / `failed`。

## 已知读数

- 8 次参考门禁全部 100%，scorer 侧可复现参考实现。
- 16 次运行为 `error`。其中 14 次同因：目标依赖未出现在 `dependency:list` 输出中，即该库没有安装到本地 Maven 仓库，`provenance` 探针据此判为解析到候选工作区之外；余 2 次为分批收集报错。
- 目标依赖在错误串里出现两种写法：包根（`org.markline`、`org.versionway`）与 Maven artifactId（`markline-core`、`plumbline-core`）。两者服务于不同检查，在去标识化后不再重合，说明见发布仓 `spec2repo` 的 `harness/lint_java.py`。
- 候选采样中多次出现双 100%（例如 `qwen-memfs`、`qwen2-classvalue`），即该题对候选没有区分度。`adjusted_gap` 非 0 的只有四次：`qwen-graphtransform` 为 1.0、`qwen2-annotvalue` 为 0.7778、`qwen-treeway` 为 0.2222、`qwen2-binarycompat-fullrepro` 为 0.1667。

## 已知缺口

`japicmp-binarycompat-fullrepro-001` 的 `tasks/japicmp-binarycompat-fullrepro-001/task.json` 没有 `mutation` 块，其变异族记录只存在于本目录 `construction/japicmp-binarycompat-fullrepro-001/spec_v1.md` 的 `INTERNAL` 头。补齐该 `task.json` 时以此文件为来源。
