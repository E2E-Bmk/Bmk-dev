# 四语言候选（Go / TypeScript / Rust / Java）

> 起于 2026-08-20。数据由调研 agent 在当日 HEAD 上实测（shallow clone 后统计），
> 非搜索摘要。LOC = 非空非注释行，排除测试、vendor、testdata 与 generated 头文件。
> 「触碰未导出」是文件级启发式，会高估。

## Go

调研环境无 Go 工具链，`go test -json` 兼容性由标准布局推断，未实际执行。

| 排名 | Repo | LOC | 事实源 / 投影 | 主要难度形状 | 判定 |
|---|---|---|---|---|---|
| 1 | `getkin/kin-openapi` | 18191 | 装载后的 `T` + loader 解析状态；Go 模型遍历 / YAML 重排 / Validate / 路由匹配 / 请求响应过滤 / v2↔v3 | 惰性解析引用图（教科书级：`SchemaRef` 在 `ResolveRefsIn` 前后行为不同）、带路径的环检测、JSON Pointer 规则重实现 | KEEP |
| 2 | `zclconf/go-cty` | 13667 | Type/Value 全域（unknown / refinement / null / mark）；json / msgpack / gocty / convert / stdlib / path | **等价判定最深**：`Value.Equals` 返回 *Value*（本身可为 unknown）vs `RawEquals` 返回 bool vs `Type.Equals` vs `TestConformance`；refinement 代数 | KEEP |
| 3 | `casbin/casbin` v3 | 9661 | Model + RoleManager 链接图；Enforce / RBAC 传递闭包查询 / 管理 API / adapter 往返 / watcher / frontend JSON | 引用图链式追踪与环容忍、模型 DSL 与 effect 聚合规则重实现 | KEEP（匹配器求值外包给 `casbin/govaluate`，该规则不在仓内）|
| 4 | `kubernetes-sigs/structured-merge-diff` | 7575 | `TypedValue` + `fieldpath.Set` 所有权账本；合并对象 / managed-fields / Compare / 冲突报告 / Extract | 等价判定即全部意义（误判 = 虚假冲突）、SSA 合并语义重实现 | KEEP（`merge/` 测试依赖 `internal/fixture` 的操作 DSL，重建边界须含它）|
| 5 | `go-task/task` | 10359 | 合并后的 Taskfile AST + 磁盘上的 `.task/` 指纹；CLI stdout / `--json` / 磁盘状态 / Executor API | 配置因子积（matrix 展开）、等价判定（是否已满足）、惰性变量图 | 边缘 KEEP —— 213 个 `.golden`，golden 相关文件占 140/240 测试函数，逼近 70% 线 |
| 6 | `expr-lang/expr` | 17344 | AST → 类型化 AST → 优化 AST → VM Program；Run / 类型错误 / 反汇编 / ast.Dump / docgen | 规则重实现（优先级、reflect 类型推断、常量折叠） | KEEP，形状比 1-5 窄；零外部依赖，测试卫生极好 |
| 7 | `vektah/gqlparser` | 7259 | 文档 + Schema，validator 回填指针；AST / Schema / 带位置的校验错误 / formatter 往返 | 惰性解析引用图 | 弱 KEEP —— GraphQL 校验是公开规范，规则可枚举，**饱和风险高** |
| 8 | `hashicorp/hcl` v2 | 22545 | `hclparse.Parser` 缓存的 Body/AST；gohcl / hcldec / hclwrite 保格式往返 / json 子语法 / 诊断 | 等价（原生 vs JSON 语法须解码一致）、≥4 投影 | **REJECT** —— 外部测试仅 252 行 vs 内部 33186 行，59 个内部测试文件中 30 个触碰未导出 |

已否决：`go-memdb`（2615 行不足）、`google/wire`（全 golden）、`go-jsonnet`（2324 个 golden）、
`hashicorp/raft`（外部测试 0 行）、`pb33f/libopenapi`（67570 行过大，149k 测试行中 147k 内部）、
`kustomize`（核心在 `api/internal/*`）、`bleve`（75749 行）、`cel-go`（Bazel + 封闭规范）、
`x/mod`（工具集合形状）、`koanf`（3988 行但过薄）、`go-openapi/analysis`（单算法）。
备选：`google/starlark-go`（13981 行，78% 外部测试，冻结语义 + 编译产物往返，但仅 67 个测试函数）。

## TypeScript

调研 agent 对前 5 名实跑了 `vitest run --reporter=json`（非静态推断）。快照占比 =
`toMatchSnapshot`/`toMatchInlineSnapshot` 计数 ÷ `it`/`test` 计数。

| 排名 | Repo（交付单元）| LOC | 事实源 / 投影 | 主要难度形状 | 判定 |
|---|---|---|---|---|---|
| 1 | `graphql-hive/graphql-inspector`（`packages/core`）| 6935 | 一对 schema（+ operation 文档）归约成带 path、criticality、typed meta 的 `Change[]`；`diff()` / `coverage()` / `similar()` / `validate()`，外加同仓 `packages/patch` 的 `patch(A, diff(A,B)) ≡ B` 往返 | 等价判定（本体就是「B 还是不是 A 的意思」）+ 规则重实现（输出协变 / 输入逆变、非空与列表包装、指令位置）+ **跨投影耦合**：`considerUsage` 让 diff 结果依赖 coverage 投影 | **KEEP，首选** |
| 2 | `APIDevTools/json-schema-ref-parser` | 5495 | `$Refs` 注册表（URL → `$Ref`）；`parse()` / `resolve()` / `dereference()`（含真实 JS 环）/ `bundle()` | 惰性解析引用图，教科书级（`$Ref.value` 解析前后不同，`Pointer.circular`/`chainCircular` 做链式追踪与环检测）；等价判定（bundle 与 dereference 须指同一 schema）| KEEP，但**单概念 + 公开规范**（JSON Reference / `$id` base-URI），是本列表里最像 python-fire 的一个 |
| 3 | `changesets/changesets` | 9186 | changeset 文件 + workspace 包图 + config（`linked`/`fixed`/`ignore`/`updateInternalDependencies`）+ `pre.json`；`assembleReleasePlan()` 对象 / `applyReleasePlan()` 落盘的 package.json+CHANGELOG / `status --output` JSON / pre 状态文件 | 规则重实现（bump 向依赖者传播、`^`/`~`/pinned/`workspace:` 区间类型保持）+ 配置因子积 + **持久磁盘状态投影** | **结构性否决**：交付面是一个 monorepo 的多个包，而 harness 的 `env.target_modules` 把候选装成单个 `file:` 包 —— 形状很好但装不进去 |
| 4 | `sverweij/dependency-cruiser` | 17931 | 一个 `ICruiseResult`；20+ reporter（json/dot/mermaid/d2/csv/markdown/teamcity/error-html/metrics/anon/baseline/html）+ `--cache` 磁盘状态 | 惰性解析引用图（`couldNotResolve`/`coreModule`/`followable` 解析后才存在）+ 环检测 + 可达性规则 + config `extends` 链；**投影数本列表最多** | KEEP，**指定为 1 号饱和时的升级目标**：其规则 DSL（`forbidden`/`allowed`/`required` × `from`/`to`/`pathNot`/`reachable`/`dependencyTypes`）完全是自创，无公开规范可背 |
| 5 | `statelyai/xstate`（`packages/core`）| 15441 | 状态节点树 + actor 注册表；纯 `transition()` / 活 actor `subscribe` / `getPersistedSnapshot()` 往返 / `@xstate/graph` 路径枚举 | 规则重实现（SCXML 语义：层级与并行配置解析、按文档序解冲突、进入退出集计算、无事件微步）| KEEP 但**记忆风险最高** —— xstate 是最知名的 TS 库之一，强模型很可能靠回忆而非靠 spec 复原 |
| 6 | `google/wireit` | 12890 | 脚本配置 DAG + `.wireit/` 指纹状态；CLI 输出 / 指纹与缓存条目 / 声明的 output 文件 / language-server 诊断 | 等价判定极纯（「这个指纹和存下来的等价吗」→ fresh / 复用缓存 / 重跑）| 备选，**runner 摩擦最大**：测试用自制 `WireitTestRig` 真的 spawn 子进程，`pnpm test` 还要拉 Electron |
| 7 | `Unleash/unleash-client-node` | 4262 | toggle 仓库 + 磁盘备份；`isEnabled` / `getVariant` / 定义列表 / metrics 桶 / 事件流 | 规则重实现（策略与约束求值、murmurhash 分桶粘性）；`@unleash/client-specification` 是跨语言一致性套件，可直接当外部行为规范复用 | 弱 KEEP，「小而易」的一档 —— 引用图很浅，核心工作是 HTTP 轮询，测试重度依赖 nock |
| 8 | `webpack/enhanced-resolve` | 10112 | `CachedInputFileSystem` + 插件流水线；async/sync resolve、`resolveContext` 依赖集合、trace 输出 | 规则重实现（`exports`/`imports` 条件解析、alias、mainFields、symlink）| **倾向否决**：Node 模块解析与 `exports` 字段是公开标准，正撞硬门；测试也常伸进 `../lib/*` |

已否决（附致命指标）：`syncpack`（已改用 Rust，npm 包只是二进制壳）、`Redocly/redocly-cli`（46816 行 `.snap`）、
`unocss`（快照 47%）、`vega-lite`（34.6k 行且测试深入 `src/compile/selection/*`）、
`arethetypeswrong/core`（形状完美但只有 23 个测试）、`publint`（40 个测试）、`awilix`（2685 行不足）、
`aws/constructs`·`eslint/config-array`·`cdk8s-core`（不足 3000 行）、`hyperjump-io/json-schema`（封闭标准 + 官方一致性套件）、
`typedoc`（46.2k + puppeteer）、`kysely`（docker-compose 数据库）、`knip`（35.7k + bun/node:test）、
`launchdarkly/js-core`（53k 且测试进 `src/evaluation/Evaluator`）、`apollo/federation`（45.9k，快照 20%）、
`typebox`（Deno 优先，无根 package.json）、`hyperformula`（karma/Chrome + TS 4.0）、`InversifyJS`（v7 是 69 行壳）、
`orama`（tap runner）、`dbml`（897k 行是生成的 parser）、`spectral`（jest + karma/Chrome，列为储备）。

---

## 可行性实测（2026-08-20，在 benchmark 自己的镜像里跑，非静态推断）

| 语言 | 候选 | 镜像 | 结果 |
|---|---|---|---|
| Go | `zclconf/go-cty` @ `0d1eb26` | `spec2repo-go:latest`（go1.26.7）| `go build ./...` 通过；`go test ./cty/... -json` → **507 个顶层测试全过，9 个包** |
| Rust | `guppy-rs/guppy` @ `2deddd3` | `spec2repo-rust:latest`（rustc 1.95.0）| `cargo nextest list -p guppy` → **68 个用例**，suite `['guppy','guppy::graph-tests']` |
| Java | `siom79/japicmp` @ `5186e1d` | `spec2repo-java:latest`（Temurin 21.0.11）| `mvn -pl japicmp -am -DskipTests package` → **BUILD_OK** |
| TypeScript | `graphql-inspector` @ `7180fca` | `spec2repo-typescript:latest`（node 22.23.2）| `vitest run packages/core` → **200 个测试全过，22 个文件** |
| TypeScript | `json-schema-ref-parser`（备选）| 同上 | **531 个测试，525 过 / 0 失败 / 6 skip，77 个文件** |

镜像已升级并推到 `:latest`（旧版保留为 `:pre-upgrade` 以便回滚）：
`spec2repo-go` 1.23 → **1.26.7**，`spec2repo-rust` 1.83 → **1.95.0**。
升级后 `tests/test_language_probes.py -m docker` 5 项全过（27s），计数未变。

**注意 vitest 版本错位**：镜像全局装的是 vitest 2.1.9，而上游候选各自锁 3.0.9 / 4.1.11。
这不影响评分——oracle 是我们自己写的独立包，按 2.1.9 的 API 写即可；只是不能用 3/4 才有的断言。

## Rust

调研环境无 cargo，编译时间是按 lockfile 的 `[[package]]` 数估的。快照占比 =
`insta::` / `assert_*_snapshot` / `expect![` / `expectorate` 的正则计数 ÷ `#[test]` 计数。
**更正一条**：`facebookincubator/cargo-guppy` 已归档重定向，活的仓库是 `guppy-rs/guppy`。

| 排名 | Repo / crate | LOC | 事实源 / 投影 | 主要难度形状 | 判定 |
|---|---|---|---|---|---|
| 1 | `guppy-rs/guppy`（crate `guppy`）| 8585 | `PackageGraph`；PackageQuery 遍历 / FeatureGraph / CargoSet 构建模拟（target 与 host 分离）/ Summary TOML + SummaryDiff / CLI / hakari 生成的 Cargo.toml | **唯一同时干净具备三种形状的候选**：规则重实现（Cargo 特性统一、v1 vs v2 resolver、自己求值 `cfg()`）+ 配置因子积（features × platform × dep-kind）+ 等价判定（SummaryDiff、`cargo-hakari verify`）；外加 `OnceCell` 背后的惰性解析 | **KEEP，最佳** |
| 2 | `oxc-project/oxc-resolver` | 6228 | `CachedPath` 缓存图（规范化路径 + package.json + tsconfig）；`Resolution` / `ResolveContext` 的 file_dependencies（文件监听投影）/ 访问器 / ResolveError | 规则重实现（Node 解析算法、`exports` 条件字段、tsconfig `extends`/`paths`、Yarn PnP）；惰性引用图（符号链接改变可观察输出，`CachedPath` 转发规范目标的元数据同时保留自身身份）；因子积 | KEEP |
| 3 | `GitoxideLabs/gitoxide`（crate `gix-ref`）| 5004 | 磁盘上的 ref store；loose 查找 / packed::Buffer 视图 / Transaction / reflog / peel | **最纯的惰性解析引用图**：`Target::Symbolic` vs `Target::Object` 使 ref 在解析前后可观察行为不同，`follow()` 追链并抛 `peel::Error::Cycle`，命名空间 ref 转发底层 ref 同时保留自身名字身份。另有等价判定（loose 与 packed 覆盖必须一致）| KEEP |
| 4 | `casey/just` | 18356 | 编译后的 justfile（AST + 模块树 + 绑定表 + recipe 表 + settings）；`--dump`（just 与 JSON 两种）/ `--evaluate` / `--list` / `--fmt` / 实际执行 | 带环检测的惰性解析（变量与 recipe 各有一个 resolver）；`import`/`mod` 引用图 | KEEP 但有硬伤：`src/lib.rs` 全是 `pub(crate) use`，**没有公开 Rust API，CLI 是唯一投影面**；断言比对精确 stdout 含错误文案，过度规定 |
| 5 | `apollographql/apollo-rs`（crate `apollo-compiler`）| 15905 | `Schema` + `ExecutableDocument`，`Node<T>` 携带源位置；内省 API / DiagnosticList / 打印 / serde 往返 | 元数据转发且保留身份（type extension 并入基定义但保留自身位置）、惰性类型引用、规则重实现 | 标记 KEEP：expect-test 占约 47%，且 **GraphQL 是封闭标准，饱和风险真实** |
| 6 | `cobalt-org/liquid-rust` | 13975 | 解析后的 Template + Runtime 变量栈 + Partials 注册表 | partial 链、词法作用域栈、过滤器链；等价判定弱 | 较弱 KEEP —— 模板引擎是饱和模式 |
| 7 | `cberner/redb` | 23086 | 数据库文件本身；读写事务 / Savepoint / DatabaseStats / check_integrity / 磁盘格式兼容 | 真实持久共享状态，但等价判定与引用图形状**弱** | 备选 —— 蹭到「避开基础设施原语」那条线 |
| 8 | `BurntSushi/ripgrep`（crate `ignore`）| 4093 | gitignore 匹配器层级 | —— | **REJECT**：测试是 `src/` 内的 `#[cfg(test)]`，能够到内部；gitignore 语义是高饱和的事实标准 |

已否决（附致命指标）：`resolvo`（117 insta / 120 测试，快照主导）、`nextest`（545 快照断言，且与本 harness 循环依赖）、
`minijinja`（191/333）、`salsa`（167 expect-test + 440 处 unsafe）、`tera`（`tests/` 仅 368 行）、
`typify`（expectorate 主导）、`nickel`（56975 行过大）、`jrsonnet`（31k 行但只有 77 个测试函数）、
`cargo-mutants` / `cargo-hack`（测试要 shell 出去跑 cargo，极慢）、`pubgrub`（自述纯算法 crate）、
`fluent-rs`（最大 crate 仅 1697 行，不足 3000）、`Figment`（`tests/` 仅约 16 个函数）、
`config-rs`（难度形状弱）、`n2`（快照测试需要一个没入库的 Google Drive zip）。

**待验证**：`oxc-resolver` 要 edition 2024 + rust 1.95，`gix-ref` 要 edition 2024 + rust 1.85。
必须先确认 `docker/Dockerfile.rust` 里的工具链版本够不够。`guppy` 是 edition 2021 / MSRV 1.56，最宽松。
`guppy` 唯一的坑是 workspace 成员 `internal-tools/cargo-compare` 依赖带 `vendored-libgit2` 的 `cargo`
（C 依赖 + cmake，524 个 lockfile 包的来源）——限定 `-p guppy -p fixtures` 后只剩约 23 个纯 Rust 依赖。

## Java

LOC = `src/main/java` 下的非空行，排除测试、资源与生成代码（生成物落在 `target/`）。
未实跑构建，「离线干净」是静态分析结论。克隆留在 `/tmp/b2r`（262 MB）。

| 排名 | Repo | LOC | 事实源 / 投影 | 主要难度形状 | 判定 |
|---|---|---|---|---|---|
| 1 | `siom79/japicmp` | 12622（核心模块）| `JApiClass` 比较树（新旧类层级合并为一个模型，每个元素带 `JApiChangeStatus` + `JApiCompatibilityChange`）；Java 模型 API / stdout / XML+XSLT→HTML / Markdown / **`SemverOut` 从同一棵树导出 MAJOR·MINOR·PATCH** / Maven 插件裁决 | **同时命中三种形状**：等价判定（本体就是它，误报是已知失效模式）+ **语言规则重实现**（JLS 第 13 章二进制兼容性、桥接方法、泛型擦除、继承方法解析，**没有委托给编译器**）+ 惰性引用图（父类接口链经 javassist `ClassPool` 解析；父类不在 classpath 时兼容性裁决**不同**）| **KEEP，首选** |
| 2 | `apache/maven-resolver` | 60315（api+spi+util+impl+named-locks）| `DependencyNode` 树，经 `DependencyGraphTransformer` 重写；CollectResult / classpath 串 / 文本树（带 `(version managed from X)` 与胜者标注）/ 本地仓库文件状态 / 事件流 | 按仲裁规则解冲突（`ConflictResolver` + `NearestVersionSelector` + `JavaScopeSelector`）；惰性引用图（verbose 模式保留败者节点，它们携带 `NODE_DATA_WINNER`——**转发他人元数据同时保留自身身份**；制品重定位；环检测有专用 fixture）| KEEP，须限定模块（交出 `api`+`spi`，重建 `impl`+`util`）|
| 3 | `google/jimfs` | 10772 | 内存文件树（`File`/`Directory`/`DirectoryEntry`/`HeapDisk` + `FileSystemView`）；Path API / Files 静态 API / 六种属性视图 / 通道与流 / WatchService / SecureDirectoryStream / URL | 规则重实现（POSIX 与 Windows 文件系统语义自己实现而非委托）；带环检测的惰性引用图（符号链接链、ELOOP）；等价判定（`PathNormalization` 的 NFC/NFD + 大小写折叠决定两个路径是否指同一文件）；配置因子积（`unix()/osX()/windows()` × Feature 集 × 归一化集）| KEEP 但**主要短板是测试白盒**：52 个测试文件里只有 8 个调 `Jimfs.newFileSystem`，其余按包私有内部类命名；按方法计公开 API 集成测试约占 40-45%。且是 JUnit 4 |
| 4 | `classgraph/classgraph` | 25685（核心）| `ScanResult` 关联图；ClassInfoList 查询 / JSON 序列化反序列化 / GraphViz dot / ResourceList | 惰性引用图（`setScanResult` 扫描后回连，未扫描的 `ClassInfo` 行为不同；`TypeVariableSignature` 对外层类方法链式解析）；规则重实现（`Class-Path:` manifest 展开链、JPMS 解析顺序）；等价判定（JSON 往返须还原等价图）| 条件 KEEP。风险多：JDK 17 起步、Error Prone + NullAway 作注解处理器、ECJ 预编译步骤、**3 个测试类用 pax-url-aether 的 `mvn:` URL 联网**必须排除；`latest` 分支刚拆成 5 模块而发布的 4.8.x 是单模块，须钉 tag |
| 5 | `apache/commons-jexl` | 34727（不含 JavaCC 生成的解析器）| 脚本 AST + `JexlContext` 变量态 + 引擎缓存；求值结果 / 上下文变更 / `getParsedText()` 重渲染源码 / `getVariables()` / 带 `JexlInfo` 的错误信息 | 语言规则重实现（`JexlArithmetic` 强制转换规则、`Uberspect` 方法解析、词法作用域、pragma）| 条件 KEEP。构建要预热 `ph-javacc-maven-plugin` 的 `jjtree-javacc`，且重建意味着**要求候选写一份 `.jjt` 文法**——形状很怪，未必想要 |
| 6 | `xmlunit/xmlunit`（`xmlunit-core`）| 9059 | 成对 DOM 遍历状态（比较序列 + Difference 列表 + 节点匹配裁决）；Diff 结果对象 / 监听器事件流 / 可读描述 / 每个差异的 XPath | 等价判定，本列表里**最纯**的一例（`ElementSelector` + `DifferenceEvaluator` + `NodeMatcher` 共同裁定「同义」，过度报告是经典 bug）| 边缘 KEEP。它用 JDK 的 `javax.xml` 解析，本身不是 XML 解析器，但擦着「不要 XML 解析器」那条线，且模型容易模式匹配成「XML diff」。JUnit 4，9k 行偏薄 |
| 7 | `apache/commons-configuration` | 50543 | `InMemoryNodeModel` 不可变节点树 | 被跟踪节点的间接层、`NodeCombiner` 合并规则、`DefaultExpressionEngine` 键小语言 | **倾向否决**：自带 `spring` 包且**测试编译需要 spring-core/beans/context/test**，撞「不依赖 Spring」；可选依赖面巨大；插值环处理委托给 commons-text，招牌形状被削弱 |
| 8 | `cache2k/cache2k` | 37642 | 缓存条目状态机 + 淘汰过期时钟 | —— | 备选。**JUnit 4（102 个文件）与 5（55 个）混用**；21 个模块含 `test-kotlin`（要 Kotlin 编译器）与 JSR-107 TCK（封闭标准）|

已否决：`javaparser`（120660 行且有代码生成阶段写回 core，「排除生成代码的源码行数」无法定义）、
`caffeine`（**只有 Gradle**，TestNG + 自制组合测试框架）、`jgit`（Bazel/Maven 混合 + 网络传输测试）、
`commons-scxml`（W3C 封闭规范 + 项目停滞）、`commons-imaging`（图像格式是封闭标准，184 个测试资源 51 MB，golden 主导）、
`commons-vfs`（FTP/SFTP/HTTP 测试联网）、`commons-beanutils`（形状薄、饱和度高）。
`velocity-engine` / `checkstyle` / `PMD` 未克隆，凭判断跳过，标记为未验证。

**跨语言注意**：japicmp、maven-resolver、commons-configuration 都设 `source/target=1.8`，
JDK 24+ 已移除该档——必须用 JDK 17 或 21 构建（当前镜像是 Temurin 21，正好）。
maven-resolver 要预热 `sisu-maven-plugin`；commons-jexl 要 `ph-javacc-maven-plugin`；
Apache Commons 系继承 `commons-parent`，会拉一长串插件（rat、checkstyle、clirr、spotbugs），需关掉这些 profile。
所有候选都无 JNI；只有 classgraph 有注解处理器。

---

## 难度校准：batch-15 上 qwen3.8-max 的实测分布

均值 37.6%，中位 34.1%，题目规模 60-75 个测试。**过 50% 的五道全部是「单概念 + 高饱和」**：

| 太容易 | 分数 | 为什么 |
|---|---|---|
| python-fire | 70.0% | 对象内省生成 CLI，Google 的知名库，单一概念 |
| dogpile.cache | 69.4% | 缓存装饰器，饱和模式 |
| poethepoet | 66.2% | pyproject.toml → 命令的简单映射 |
| textx | 63.3% | 文法/DSL，形状众所周知 |
| python-semantic-release | 55.4% | conventional commits → 版本号，**规则是公开标准** |

| 足够难 | 分数 | 为什么 |
|---|---|---|
| pony | 4.5% | ORM 查询反编译，语义非常规 |
| celery | 4.5% | 分布式任务队列，多对象协作 |
| frictionless-py | 6.2% | 分层 schema 推断 |
| rocketry | 20.0% | 条件调度语言 |

**结论**：决定难度的不是规模，是「核心规则是否为可记忆的公开标准」加「一个用户场景要几个对象协作」。
python-semantic-release 那 55.4% 是最值得警惕的一例——规则驱动，但规则本身是公开且可枚举的。

对四个首选的影响：
- `guppy`（Rust）—— Cargo 特性统一与 v1/v2 resolver 的差异**没有可记忆的规范文本**，多对象，判定为难。
- `go-cty`（Go）—— unknown/refinement/mark 代数是该库独有，判定为难。
- `graphql-inspector`（TypeScript）—— **中风险**。类型系统兼容性规则（协变/逆变）源自 GraphQL 规范，
  可部分背诵；但 criticality 分级与 `considerUsage` 降级是库自创策略，且解析本身外包给 `graphql` 包。
  超 50% 则换 `dependency-cruiser`——其规则 DSL 完全自创，无规范可背，且投影数最多。
- `japicmp`（Java）—— **风险点**：JLS 第 13 章是公开标准，形状接近 python-semantic-release。
  但二进制兼容性规则远比 conventional commits 繁复，且六个投影带来集成负担。列为中风险，
  评分后若超 50% 则换 `maven-resolver`（依赖仲裁，多对象，几乎不可能记忆，但需模块限定）。


镜像现状 vs 候选要求（**已于 2026-08-20 升级完毕**）：

| 语言 | 升级前 | 升级后 | 候选要求 | 结论 |
|---|---|---|---|---|
| Go | `golang:1.23-bookworm` | **`golang:1.26-bookworm`** | go-cty `go 1.25`、kin-openapi `go 1.25`、structured-merge-diff `go 1.23` | 已解锁 |
| Rust | `rust:1.83-bookworm` | **`rust:1.95-bookworm`** | guppy edition 2024；oxc-resolver 1.95；gix-ref 1.85；just 1.89 | 已解锁 |
| TypeScript | `node:22-bookworm` | 未变 | graphql-inspector 无特殊要求；全局 vitest 2.1.9 与上游 3/4 错位，只影响 oracle 写法 | 可用 |
| Java | `maven:3.9-eclipse-temurin-21` | 未变 | japicmp 需 JDK ≤23；上游用 JUnit 6.0.1，oracle 由我们自己写，版本自定 | 可用 |

升级镜像的风险极低：非 Python 题目当前为零，不存在回归面。nextest 是从
`get.nexte.st` 取预编译二进制（`Dockerfile.rust:29`），刻意不绑 rustc 版本，升级不受影响。
