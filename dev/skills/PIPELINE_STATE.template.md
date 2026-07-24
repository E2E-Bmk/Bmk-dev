# Pipeline State — {TASK_ID}

> **使用规则**
> - 只修改 `## Current` 块。`## Catalogue` 是只读参考，不要编辑。
> - 每次转移状态：更新 `state`，追加一行到 `## History`，把 `todo` 替换为新状态的 catalogue todo。
> - 循环时：`state` 写回循环目标，`todo` 重置为该状态的 catalogue todo，对应 `*_iter` 加一。
> - `*_iter > 2` 且未解决 → 停止，上报 orchestrator，不得继续转移。

---

## Current

```
state:      S1_SCREENING
stage:      1
spec_iter:  0
filter_iter: 0
eval_iter:  0
updated:    {DATE}
```

todo:
- [ ] 执行 import pre-screen: `grep -rn "from <pkg>\._\|import <pkg>\._" tests/`
- [ ] 填写 filter_notes.md 所有字段
- [ ] 设置 decision: keep | defer | reject

---

## History

| # | date | from | to | note |
|---|------|------|----|------|

---

## Forbidden Transitions（任何状态下均适用）

- `S3B_TRIGGER` 要求 `filter/rewrite_audit.md` 存在 — 否则回 `S3A_REWRITE`
- `S3_ORACLE_MERGE` 要求 `kept_upstream.txt` 或 `generated_tests.py` 至少一个存在
- `S4_SETUP` 要求 `filter/reference_score.json` 存在且 pass rate = 100%
- `S5_JUDGE` 要求 `candidate-runs/.../score_result.json` 存在

---

## Catalogue（只读）

### S1_SCREENING
```
entry_requires: wip/{task}/ 目录已创建
todo:
  - [ ] 执行 import pre-screen: grep -rn "from <pkg>\._\|import <pkg>\._" tests/
  - [ ] 填写 filter_notes.md 必填字段:
        repo, source_path, commit, src_loc, test_functions, test_files,
        dominant_test_styles, public_docs, core_fact_source, derived_views,
        external_deps, test_import_audit (clean|HIGH_RISK + 估计%),
        docs_test_alignment (aligned|MISMATCH),
        contamination_note ({repo}@{version}, released {date}, cutoff relation),
        decision (keep|defer|reject), reason, risks
  - [ ] 设置 decision
exit_artifact: filter_notes.md（所有字段填写完整）
→ S1_SELECTED       (decision = keep)
→ RETIRED           (decision = reject, terminal)
```

### S1_SELECTED
```
todo:
  - [ ] 在 CANDIDATES.md 追加 SELECTED 行
exit_artifact: CANDIDATES.md 行
→ S2_SPEC_DRAFT
```

### S2_SPEC_DRAFT
```
todo:
  - [ ] 读 __init__.py / __all__，产出 public API surface list
  - [ ] 逐项过 Q1/Q2 判断
  - [ ] 写 spec_vN.md 草稿（含 internal header）
exit_artifact: spec_vN.md
→ S2_SPEC_CHECK
```

### S2_SPEC_CHECK
```
todo:
  - [ ] Check 1: 每个 feature 可追溯到公开文档？
  - [ ] Check 2: 无内部类名或未导出 module path？
  - [ ] Check 3: invariants 用行为语言（非代码）？
  - [ ] Check 4: Non-goals 明确列出？
  - [ ] Check 5: 无隐含 fixture shape？
  - [ ] Check 6: 所有行为语句用 must/returns/raises，无 can/may？
  - [ ] Check 7: 所有条件行为已显式写出条件（must when [X]，非"when applicable"）？
  - [ ] Check 8: 每个行为描述了 failure path（违反前置条件时 must raise / must return 什么）？
  - [ ] Check 9: 有 Product State Model 节（或等价结构），含 ≥3 条跨视图不变量？
  - [ ] Check 10: 无 escape hatch（措辞模糊到候选可跳过某行为而仍满足 spec 表述）？
→ S2_SPEC_DONE      (全10条通过)
→ S2_SPEC_DRAFT     (loop: 任意一条失败; spec_iter += 1; spec_iter > 3 → 上报)
```

### S2_SPEC_DONE
```
todo:
  - [ ] 剥离 internal header，确认 candidate packet 就绪
→ S3A_IMPORT_AUDIT
```

### S3A_IMPORT_AUDIT
```
todo:
  - [ ] 对每个 test 文件执行 import 分类（见 test-filter SKILL.md 表格）
  - [ ] 标注每个文件的 import 类型
exit_artifact: import 分类结果（写入 rewrite_audit.md 头部）
→ S3A_REWRITE
```

### S3A_REWRITE
```
todo:
  - [ ] 对每个有问题的 import，尝试 public API rewrite
  - [ ] 记录每个文件的 rewrite_result: pass | fail
  - [ ] 写 filter/rewrite_audit.md（必须存在，S3B_TRIGGER 的硬性前置）
exit_artifact: filter/rewrite_audit.md（必须包含每个被丢弃文件的 failure_reason）
→ S3A_FAIRNESS      (丢弃文件 ≤ 50%)
→ S3B_TRIGGER       (丢弃文件 > 50%; rewrite_audit.md 必须已存在)
```

### S3A_FAIRNESS
```
todo:
  - [ ] 逐 nodeid 审查：repr check? private attr? 不可追溯到文档？
  - [ ] 标记 excluded / source-only
  - [ ] 写 filter/candidate_filter_map.md（草稿，含每行 status + spec_section）
        注意：这是草稿，最终 spec_test_map.md 在 S3_ORACLE_MERGE 才写
exit_artifact: filter/candidate_filter_map.md（草稿）
→ S3A_DUMMY
```

### S3A_DUMMY
```
todo:
  - [ ] 对 kept 集合运行 dummy stub（所有公开函数 return None）
  - [ ] 丢弃通过 dummy 的测试
exit_artifact: filter/kept_upstream.txt
→ S3A_DONE          (count ≥ 30)
→ S3B_TRIGGER       (count < 30; rewrite_audit.md 必须已存在)
```

### S3A_DONE
```
→ S3_ORACLE_MERGE
```

### S3B_TRIGGER
```
entry_requires: filter/rewrite_audit.md 存在（硬性检查 — 不存在则回 S3A_REWRITE）
todo:
  - [ ] 确认 rewrite_audit.md 存在并记录了所有失败原因
→ S3B_COVERAGE
```

### S3B_COVERAGE
```
todo:
  - [ ] 对 reference 运行 coverage --branch，产出 filter/coverage.json
  - [ ] 运行 `python Bmk-dev/tools/format_coverage.py filter/coverage.json <source_root>`，产出 filter/coverage_gaps.txt
exit_artifact: filter/coverage_gaps.txt
→ S3B_GENERATE
```

### S3B_GENERATE
```
todo:
  - [ ] 给 generation agent: coverage_gaps.txt + spec_vN.md（只读 reference，不读 source）
  - [ ] agent 观察 reference 输出后写断言
exit_artifact: filter/generated_tests.py
→ S3B_DUMMY
```

### S3B_DUMMY
```
todo:
  - [ ] 对生成测试运行 dummy stubs，丢弃通过的
→ S3B_REFERENCE
```

### S3B_REFERENCE
```
todo:
  - [ ] 对生成测试运行 reference，要求 ≥ 95% 通过
→ S3B_DONE          (≥ 95%)
→ S3B_GENERATE      (loop: < 95%; filter_iter += 1; filter_iter > 2 → 上报)
```

### S3B_DONE
```
→ S3_ORACLE_MERGE
```

### S3_ORACLE_MERGE
```
entry_requires: kept_upstream.txt 或 generated_tests.py 至少一个存在
todo:
  - [ ] 合并 Track A + Track B 输出
  - [ ] 写 filter/spec_test_map.md（最终版，含 source: upstream|generated 列）
  - [ ] 写 filter/kept_nodeids.txt 和 taxonomy.jsonl
exit_artifact: filter/spec_test_map.md（最终）
→ S3_REFERENCE_RUN
```

### S3_REFERENCE_RUN
```
todo:
  - [ ] 对 oracle 运行 reference 实现，要求 100% 通过
        评分命令必须加 --remove-path <pkg>（防止系统安装包遮蔽）
  - [ ] 记录 scorer_isolation 到 task.json（毕业时生成）
exit_artifact: filter/reference_score.json
→ S3_DONE           (100%)
→ S3_ORACLE_MERGE   (loop: < 100%; fix oracle; filter_iter += 1)
```

### S3_DONE
```
→ S4_SETUP
```

### S4_SETUP
```
todo:
  - [ ] 准备 cleanroom candidate eval 环境（在 Linux 或 WSL 中运行，非 native Windows）
  - [ ] 组装 candidate packet（仅 spec body，无 test/filter 文件）
→ S4_EVAL_RUN
```

### S4_EVAL_RUN
```
todo:
  - [ ] 运行 candidate agent
exit_artifact: candidate-runs/{run}/score_result.json
→ S4_ANALYSIS
```

### S4_ANALYSIS
```
todo:
  - [ ] 检查分数分布，排查饱和/异常
→ S4_DONE
→ S2_SPEC_DRAFT     (loop: 饱和检测; spec_iter += 1)
→ S3_ORACLE_MERGE   (loop: oracle 质量问题; filter_iter += 1)
```

### S4_DONE
```
→ S5_JUDGE
```

### S5_JUDGE
```
todo:
  - [ ] Anti-cheat preflight: `python -c "import <pkg>; print(<pkg>.__file__)"`，结果写入报告
  - [ ] Solvability: reference 跑 oracle，要求 ≥ 95%
  - [ ] Fairness Gate A: spec_section spot-check（covered 行 → 验证 spec heading 存在）
  - [ ] Fairness Gate B: failure pattern audit（失败是行为缺口还是内部结构？）
  - [ ] Fairness Gate C: 若 oracle_source=generated_only，抽检 ≥5 条生成测试
        对每条验证：spec-driven（断言可从 spec 推导）+ behavioral（无 repr/内部字段）
  - [ ] Gate D: Coverage Gap Audit — 对每个 spec H2/H3 节检查 spec_test_map 是否有 covered 行
        判定：FULL（0节无覆盖）| PARTIAL（1-2个次要节）| GAP（核心 invariant 节无覆盖）
        GAP → 补充测试或在 task.json 写入 coverage_gap 字段后方可 QUALIFIED
  - [ ] 若候选 pass rate=100% 且实现文件数远少于原始包：标注 trivially-solved + saturated-candidate-score
  - [ ] 写 judge/diagnosis_report.md（含 Preflight output 块 + Gate D section，否则报告无效）
exit_artifact: judge/diagnosis_report.md
→ QUALIFIED         (所有 gate 通过, terminal)
→ S2_SPEC_DRAFT     (loop: spec gap; spec_iter += 1; spec_iter > 3 → RETIRED)
→ S3_ORACLE_MERGE   (loop: filter issue; filter_iter += 1; filter_iter > 2 → RETIRED)
→ S4_SETUP          (loop: cheat/env issue; eval_iter += 1; eval_iter > 2 → RETIRED)
→ RETIRED           (不可修复, terminal)
```

### QUALIFIED（terminal）
```
todo:
  - [ ] 执行 Graduation procedure（见 task-synthesizer SKILL）:
        1. spec_vN.md → tasks/{id}/spec.md（剥离 INTERNAL header）
        2. 按 taxonomy 拆分测试 → oracle/test_atomic.py + oracle/test_integration.py
        3. 提取测试依赖 → oracle/requirements.txt
        4. 生成 task.json（含 taxonomy, stats, scorer_isolation, weaknesses, source_meta, integration_gap）
        5. 复制 kept_nodeids.txt, taxonomy.jsonl, spec_test_map.md
        6. 运行 harness/verify_task.py {task_id} → 必须输出 QUALIFIED_VALID
  - [ ] 在 CANDIDATES.md 追加 QUALIFIED 行
```

### REOPENED_S3（non-terminal，从 QUALIFIED 转入）
```
entry_requires: QUALIFIED task 的 oracle 文件被修改
todo:
  - [ ] 在 CANDIDATES.md 现有 QUALIFIED 行追加 superseded_by: {new_oracle_version}
  - [ ] 重命名 score_result.json → score_result_superseded_{date}.json
  - [ ] 重新执行 S4_EVAL_RUN → S5_JUDGE
exit_artifact: 新的 score_result.json + diagnosis_report.md
→ QUALIFIED         (重新通过所有 gate)
→ RETIRED           (无法修复)
```

### RETIRED（terminal）
```
todo:
  - [ ] 在 CANDIDATES.md 追加 RETIRED 行，写明 failure_reason
```
