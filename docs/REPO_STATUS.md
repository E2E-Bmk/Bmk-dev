# Repo Status

> 最后更新：2026-08-23
> 用途：认领题目前查阅，避免重复工作
> 本文只记录能从仓库现状再生的事实。逐包数据不在此复制，重算命令见文末。

---

## 层级由 verdict.json 判定，不由标签声明

`tasks/{language}/{id}/` 是通过静态门禁的题包，`wip/{language}/{id}/` 是尚未通过的工作台。这条线不再由 `task.json` 里的人工标签划出，而由 `harness/core/verify_task.py` 的结论逐包写入 `verdict.json`：`tier` 是门禁算出的应属层级，`filed_under` 是它当前实际所在的层级。两者不一致时 `validate_ledger.py` 会告警，因此「已通过却仍停在工作台」与「未通过却摆在 tasks 下」都不会静默存在。

`verdict.json` 是生成物，不手工编辑。`harness/core/verdict.py --check` 重算全部题包，并把任何手改报为漂移。

当前划线：97 个题包中 72 个在 `tasks/`，25 个在 `wip/`。

## 各语言的实况差异极大

| 语言 | tasks/ | wip/ | 合计 |
|------|--------|------|------|
| python | 60 | 0 | 60 |
| java | 10 | 18 | 28 |
| rust | 0 | 7 | 7 |
| typescript | 2 | 0 | 2 |

python 与 typescript 两条线的题包全部通过静态门禁；java 通过 10/28；rust 尚无一个通过。

## 25 个未通过里，19 个栽在同一处

按门禁异议类型统计，一个题包可能同时触发多条：

| 次数 | 门禁异议 |
|------|----------|
| 24 | `depends_on` 覆盖率低于底线，多为 0/N = 0% |
| 4 | 未在 `TARGET_IMPORTS` 注册导入根 |
| 4 | taxonomy 与实际测试不匹配 |
| 1 | 层底线未达（atomic / integration 数量） |
| 1 | 可评分测试数未达底线 |

25 个中 19 个的唯一异议就是 `depends_on` 覆盖率，另 6 个触发多条。这不是个案而是系统性缺口：java 与 rust 两条线在建包时未填 `depends_on`，而 True Integration Gap 的计算依赖它。补齐属 test-filter 职责，不在台账维护范围内。

## 静态门禁通过不等于证据齐备

`verdict.json` 的 `evidence` 汇总题包已有的测量，`evidence_pending` 列出缺的。97 个题包的覆盖情况：

| 已有 | 槽位 |
|------|------|
| 74 | candidate_score |
| 72 | reference_pass |
| 36 | adjusted_gap |
| 12 | mutation |
| 7 | coverage_gap |
| 2 | dummy_pass |

`reference_pass` 缺的 25 个与降级的 25 个基本重合。真正刺眼的是 `dummy_pass`：只有 2 个题包记录过「空实现能拿多少分」这一对照，也就是说绝大多数题包从未验证过自己不是靠平凡实现就能通过。这是本仓库当前最大的证据缺口。

同一测量此前散落在三个字段名下 —— `reference_pass_rate` 56 个、`reference_score` 35 个、`reference.pass_rate` 2 个。`verdict.json` 按固定槽位收敛，并在 `from` 字段记下取自哪个原始键。

## CANDIDATES.md 的 23 个告警属既有欠账

`validate_ledger.py` 当前报 23 个告警：12 个是 `CANDIDATES.md` 的行指向已不存在的题包，8 个是同一上游仓库同时被记为 QUALIFIED 与 RETIRED，3 个是通过门禁但带告警的题包。前两类是候选台账自身的历史欠账，本次重构未改动 `CANDIDATES.md` 的行内容。

## pipeline_note 记录流水线位置，不是结论

`task.json` 里原有的 `status` 字段混装了两类信息：流水线位置（`S2_SPEC`、`REOPENED_S3`、`REVALIDATION-REQUIRED`）与门禁结论（`QUALIFIED`、`STATICALLY_VALIDATED`、`REJECTED_E1`）。因为名字叫 status，它持续被当作结论读取。该字段已改名为 `pipeline_note`，只保留溯源用途；结论一律看 `verdict.json`。`sync_task_metadata.py` 不再为它补写默认值 —— 旧代码默认补 `STATICALLY_VALIDATED`，等于在不运行门禁的情况下断言门禁结果。

## wip/ 进版本库，但只进记录

`wip/` 在磁盘上约 28G，绝大部分是 `target/`、`node_modules/` 与运行产物。`.gitignore` 对它采用白名单：只有下列四类进版本库，其余一概忽略。

| 路径 | 内容 |
|------|------|
| `wip/{lang}/{id}/BENCH.md` | 工作台说明，手写，随工作推进修改 |
| `wip/{lang}/{id}/verdict.json` | 门禁结论，生成物，勿手改 |
| `wip/{lang}/{id}/packet/**` | 题包本体，与 `tasks/{lang}/{id}/` 同构 |
| `wip/{lang}/{id}/runs/index.jsonl` | 运行索引；`runs/` 下其余产物不进库 |

当前 `wip/` 下入库 295 个文件、约 3.4M。磁盘上另有 38 个工作台未入库：它们尚无 `packet/`，不命中白名单。

## 一个题包可从两棵树中的任一棵解析

`harness/core/layout.py` 同时认 `tasks/{lang}/{id}/` 与 `wip/{lang}/{id}/packet/`。所有门禁读到的是同一个题包，因此题包可以在两层之间来回移动而测量不会失联。`tier_of()` 报告它实际在哪棵树；同一 id 若两棵树都有，`duplicates()` 会点名，且以 `tasks/` 的那份为准。

新建工作台按上表放置四件套即可，无需另立约定。

## 质量标准

- Spec 标准：`docs/SPEC_STANDARD.md`
- Oracle 标准：`docs/ORACLE_STANDARD.md`（A≥30, I≥25, T≥60, depends_on≥50%）
- 静态门禁：`docs/QUALITY_GATE.md`，由 `harness/core/verify_task.py` 实施
- 验收清单：`docs/ACCEPTANCE_CHECKLIST.md`

## 重新生成本文的数字

```bash
python3 harness/core/verdict.py --check                    # 重算全部 verdict.json，报告手改漂移
python3 harness/core/validate_ledger.py                    # 逐包静态校验 + 台账交叉检查
python3 harness/core/sync_task_metadata.py --all --check    # 检查 task.json 与 oracle 文件是否漂移
```

逐包的 Atomic / Integration 计数与 Lint、Static 结论由 `validate_ledger.py` 逐行输出，本文不再复制，以免快照与实际再次分叉。
