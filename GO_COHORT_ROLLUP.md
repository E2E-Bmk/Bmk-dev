# Go 首批题包（spec2repo-aligned-25_GO）评测与归因

## 任务介绍

本文记录 Go 语言首批 25 道题包的一次全量评测及其零分归因。题包来自外部产出的
数据集 `spec2repo-aligned-25_GO`，此前从未在本仓库的评测链路上跑过，因此这次评
测同时承担两件事：验证 Go 评分链路本身可用，以及测量这批题包的可用程度。

题包与本仓库既有形态的差异有两处。其一是 oracle 的物理布局：既有题包把两个层级
放在各自的子目录（`oracle/atomic/`、`oracle/integration/`），而这 25 道题的全部测
试位于同一个 Go 包内、共用一个 `helpers_test.go`，层级归属由题包自带的
`ROOT-MAP.json` 声明。同包共享测试辅助是 Go 的编译约束，物理拆分会直接破坏编译，
所以层级只能从声明读取。其二是目标模块的注册：Go 的 oracle 是一个独立模块，靠
`go mod edit -replace` 把目标模块指向候选工作区，若不注册这条映射，oracle 会解析
到已发布的上游版本，测的就不是候选代码。

为此新增三处基建改动：

- `harness/lang/go/target_imports.json`（新增）——25 道题到 Go 模块路径的映射。
- `harness/core/target_imports.py`——新增 `_merge_go_registrations()`，沿用 rust、
  typescript、java 三条既有支路的加载方式。
- `harness/lang/go/runner.py`——新增扁平单包模式：`ROOT-MAP.json` 存在时由声明切
  分层级、批次工作目录取 oracle 根，否则回退到既有的子目录形态。

数据口径声明：

- 模型 qwen3.8-max，agent 为 minisweagent，镜像 `spec2repo-go:latest`（go1.26.7
  linux/amd64），批次超时 300 秒，环境准备超时 900 秒，单次尝试，无重跑。
- 分母为 oracle 中的测试函数数，子测试折叠到父函数计一次。`ROOT-MAP.json` 中声明
  为 `system` 层的根并入 integration 计数，与 Python、TypeScript 的既有折叠方式
  一致。
- 评分器在批次不可用时不保留编译输出，因此每题的编译诊断是事后在同一镜像内重放
  `go build`（候选）与 `go vet`（oracle）取得的，记录于各题
  `wip/go/<id>/runs/diagnostics.json`（不入版本库）。
- 归因所依据的"规格是否描述过某符号"由脚本判定：取 oracle 测试对目标模块别名的全部
  导出选择子，在 `spec.md` 中做全词匹配。该判定只看符号名是否出现，不判断语义是否
  一致，属于宽松下界。

## 整体结果

25 道题全部 `status=error`，1433 个测试位点无一通过。

| 语言 | 题 | 均分 | a分 | i分 | 测试总数 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| go | badger-go25-004 | 0.0% | 0/16 | 0/32 | 48 | 候选 API 面与 oracle 不符 |
| go | bbolt-go25-004 | 0.0% | 0/16 | 0/32 | 48 | 候选自身不编译 |
| go | bleve-go25-002 | 0.0% | 0/32 | 0/44 | 76 | 候选 API 面与 oracle 不符 |
| go | centrifuge-memory-fullrepro-002 | 0.0% | 0/16 | 0/32 | 48 | 候选 API 面与 oracle 不符 |
| go | eventhorizon-go25-004 | 0.0% | 0/12 | 0/24 | 36 | 候选缺子包 |
| go | fx-lifecycle-fullrepro-002 | 0.0% | 0/32 | 0/43 | 75 | oracle 用到规格未描述的符号 |
| go | go-git-go25-002 | 0.0% | 0/16 | 0/32 | 48 | 候选缺子包 |
| go | go-task-go25-002 | 0.0% | 0/16 | 0/32 | 48 | 候选 API 面与 oracle 不符 |
| go | go-workflows-go25-002 | 0.0% | 0/32 | 0/47 | 79 | 候选缺子包 |
| go | go25-v18-koanf-config | 0.0% | 0/32 | 0/32 | 64 | oracle go.mod 相对 replace 悬空 |
| go | go25-v19-ent-schema-codegen | 0.0% | 0/32 | 0/32 | 64 | 候选 API 面与 oracle 不符 |
| go | go25-v20-templ-compiler-runtime | 0.0% | 0/32 | 0/32 | 64 | 候选 API 面与 oracle 不符 |
| go | go25-v21-containerregistry-image-graph | 0.0% | 0/32 | 0/32 | 64 | 候选缺子包 |
| go | go25-v22-alertmanager-routing-lifecycle | 0.0% | 0/32 | 0/32 | 64 | 候选 API 面与 oracle 不符 |
| go | go25-v23-mvdan-sh-syntax-runtime | 0.0% | 0/32 | 0/32 | 64 | 候选 API 面与 oracle 不符 |
| go | go25-v24-kustomize-local-build | 0.0% | 0/32 | 0/32 | 64 | 候选缺子包 |
| go | hashicorp-raft-go25-003 | 0.0% | 0/8 | 0/15 | 23 | oracle 用到规格未描述的符号 |
| go | memberlist-gossip-fullrepro-003 | 0.0% | 0/32 | 0/40 | 72 | 候选 API 面与 oracle 不符 |
| go | nutsdb-go25-005 | 0.0% | 0/16 | 0/32 | 48 | oracle 用到规格未描述的符号 |
| go | oras-artifact-graph-fullrepo-001 | 0.0% | 0/32 | 0/32 | 64 | oracle 用到规格未描述的符号 |
| go | pebble-go25-002 | 0.0% | 0/16 | 0/32 | 48 | 候选缺子包 |
| go | protoactor-lifecycle-fullrepro-002 | 0.0% | 0/16 | 0/32 | 48 | oracle 用到规格未描述的符号 |
| go | ristretto-go25-008 | 0.0% | 0/16 | 0/32 | 48 | 候选 API 面与 oracle 不符 |
| go | serf-query-fullrepro-003 | 0.0% | 0/32 | 0/32 | 64 | 候选 API 面与 oracle 不符 |
| go | watermill-router-fullrepro-003 | 0.0% | 0/32 | 0/32 | 64 | 候选缺子包 |
| go | **合计 25 题** | **0.0%** | 0/612 | 0/821 | 1433 | 全部 status=error |

零分不等于链路失效。三项检查表明评分链路按预期工作：分母被正确枚举（例如
bbolt 题得到 atomic 16 与 integration 32，与题包 `task.json` 声明一致）；模块来源
审计通过，bbolt 题的 provenance 记录为
`{"name": "go.etcd.io/bbolt", "paths": ["/eval/workspace"]}`，说明 `replace` 生效
而非落到已发布版本；oracle 自身的依赖解析与 `go mod tidy` 在 24 道题上无报错。

零分的直接原因统一为一种：oracle 测试包编译不通过，因而没有产生任何测试事件，评
分器将该批次记为不可用，文案为 `N/N batches had collection/report errors
(invalid score)`。以下按编译中断的位置分类。

## 分类归因

### 候选 API 面与 oracle 不符（11 题）

编译在 oracle 引用某个候选符号时中断，而该符号名在规格中出现过。这是候选实现与规
格声明的形状不一致，属候选侧问题。例如 bleve 题的
`helpers_test.go:28:13: undefined: bleve.NewIndexMapping`，go-task 题的
`helpers_test.go:62:64: multiple-value task.NewExecutor(options...) ... in
single-value context`（候选把返回值定成单值，规格与 oracle 按双值使用），ristretto
题的 `fork_test.go:31:3: unknown field IgnoreInternalCost in struct literal of
type ristretto.Config[string, string]`。

### 候选缺子包（7 题）

编译在模块解析阶段中断：候选模块存在且 `replace` 生效，但不含 oracle 需要的子包。
例如 go-git 题报
`module github.com/go-git/go-git/v5@latest found (v5.19.2, replaced by
/eval/w), but does not contain package
github.com/go-git/go-git/v5/plumbing/object`。这些题的 oracle 跨多个子包取用目标
模块，候选只产出了根包与部分子目录。

### oracle 用到规格未描述的符号（5 题）

编译中断处的符号在 `spec.md` 中不曾出现，候选无从推断。例如 fx 题需要
`fx.NopLogger`、hashicorp-raft 题需要 `raft.InmemStore`、oras 题需要 `Pusher`、
protoactor 题需要 `WithDispatcher`、nutsdb 题需要 `DataStructure`。这五题的零分不
能计到候选侧。

### 候选自身不编译（1 题）

bbolt 题的候选工作区存在重复声明：`bucket_api.go:4:6: Bucket redeclared in this
block`，同一类型与方法在 `bucket.go` 和 `bucket_api.go` 各写了一份。该错误在评分器
的 `install_log_tail` 中已完整保留。

### oracle go.mod 相对 replace 悬空（1 题）

koanf 题的 oracle `go.mod` 含 12 条相对路径 `replace`，除目标模块那条会被运行器覆
盖外，其余 11 条（`koanf/maps`、`koanf/parsers/json` 等同仓库兄弟模块，以及四个第
三方模块的本地副本）指向出题时的目录 `../../reference/...`，题包本身不携带该目录，
于是报 `github.com/knadh/koanf/parsers/json@v0.0.0: replacement directory
../../reference/parsers/json does not exist`。该题在当前形态下无法评分，与候选无关。

## 需要披露的一项结构性差异

25 道题中有 14 道，其出题材料里的 `TASK.md` 要求在"给定/指定的源码树"上实现规格，
例如 bbolt 题写作"in the assigned bbolt source tree. Preserve existing public
behavior and repository tests"，eventhorizon 题写作"in the supplied Event Horizon
source tree"。对应的 `REFERENCE-PROVENANCE.json` 也记录了上游仓库、版本与提交号，
例如 hashicorp-raft 题为 `github.com/hashicorp/raft` 的 `v1.7.3` /
`c0dc6a0b2c7e889f31e5ab2f7ed90ceb159acffe`。

本仓库的评测链路不做仓库播种：`harness/evaluate.py` 为每道题创建空工作区，候选完
全依据规格从零构建。这是既有设计，`repo` 与 `repo_commit` 两个字段在 harness 中没
有任何读取方。因此这 14 道题在当前链路下被当作从零构建题评测，其"候选缺子包"与部
分"API 面不符"的失败中，有多少源于口径差异、有多少源于候选能力不足，单凭本次数据
无法拆分。上文的分类只陈述编译中断的位置，不越过这条界线做程度判断。

同时说明另外三项对结论不利的信息：其一，本次为单次尝试，无重跑，个别题的候选质量
可能受该次采样影响；其二，评测期间模型配额受限，出现过重试等待，但重试由客户端完
成，未观察到因此产生的失败；其三，题包转换时丢弃了 4 道题的 `MUTATION-PORTFOLIO.md`
（出题元数据，非评测输入），且 koanf 题原本不带 `go.sum`。

## 合并结论

三条结论按证据强度排列。

第一，Go 评分链路可用。分母枚举、模块来源审计、层级切分三项均在 25 道题上按预期
工作，扁平单包模式与既有子目录形态并存且互不干扰。

第二，这批题包目前不适合作为可评测题包呈现。25 道题全部未通过静态门禁
（`harness/core/verify_task.py` 报缺少语义章节、层级底线、taxonomy 与 depends_on
覆盖率等），且其中 6 道题存在与候选无关的题包缺陷：5 道题的 oracle 引用规格未描述
的符号，1 道题的 oracle 依赖出题时的目录布局。因此 25 道题落在 `wip/go/` 而非
`tasks/go/`，每道题的 `verdict.json` 由 `harness/core/verdict.py` 生成，`tier` 与
`filed_under` 均为 `wip`。

第三，存在一处口径不匹配，其影响范围尚未测量。14 道题按增量修改设计、按从零构建
评测，这一点已在上节披露，但它对分数的贡献比例需要一次播种上游源码树的对照评测才
能确定。

## 改进方向

题包侧：

1. koanf 题——移除 oracle `go.mod` 中 11 条指向出题目录的 `replace`，或把兄弟模块
   与第三方本地副本一并纳入题包。
2. 上述 5 道 oracle 引用规格未描述符号的题——补齐规格中的公共面，或从 oracle 中移
   除对未描述符号的引用。
3. 全部 25 道题——按静态门禁的章节与 taxonomy 要求补齐 `spec.md` 与 `task.json`，
   通过后方可从 `wip/go/` 迁至 `tasks/go/`。

链路侧：

4. 若决定支持增量修改口径，需在 `harness/evaluate.py` 中按 `task.json` 的 `repo` /
   `repo_commit` 播种工作区，并在评分记录中标注该题以何种口径评测；这是新增能力，
   不应默认开启。
5. 评分器在批次不可用时丢弃报告文本，Go 的编译诊断正写在该文本中。建议在
   `harness/sandbox.py` 的 `_run_suite` 中保留该文本的尾部，避免每次归因都要事后
   在容器内重放。
