# Bmk-dev 开发目录结构提案

> 目标：保持流水线可用、评测可跑的前提下，消除散落文件、明确每个目录的职责
> 原则：每个目录有且只有一个职责，根目录零散文件不超过 5 个

---

## 提案结构

```
Bmk-dev/
│
├── tasks/                        # [产物] 已合格 task 的正式交付件
│   └── {task-id}/
│       ├── spec.md               # 行为规格（候选模型唯一输入）
│       ├── oracle/               # 评测用测试（从 wip 毕业时复制过来）
│       │   ├── tests.py          # generated_tests.py 或 rewritten 的合并
│       │   ├── conftest.py       # 如需
│       │   └── deps.txt          # 测试依赖（pytest-xxx 等）
│       ├── task.json             # 元数据总控（替代 MANIFEST + taxonomy + kept_nodeids）
│       └── CHANGELOG.md          # 本 task 的变更记录（spec 版本、oracle 变更、审计）
│
├── wip/                          # [工作区] 流水线进行中的 task
│   ├── _template/                # 新 task 模板
│   └── {task-id}/
│       ├── PIPELINE_STATE.md
│       ├── spec/                 # spec 迭代版本
│       ├── filter/               # 测试过滤产物（generated_tests.py 等）
│       ├── judge/                # 判定报告
│       └── candidate_task/       # 公开包组装
│
├── runs/                         # [评测记录] 所有模型评测的完整轨迹
│   └── {model}-{task}-{specver}-{date}-{seq}/
│       ├── prompt.md             # 模型实际输入（= spec 快照）
│       ├── output/               # 模型产出代码
│       ├── score.json            # 评分结果
│       └── meta.json             # 运行环境（platform、python、isolation）
│
├── harness/                      # [工具] 评分和执行脚本
│   ├── scorer.py                 # pytest runner（原 score_pytest_original.py）
│   ├── runner.py                 # 端到端评测入口（原 run.py）
│   ├── verify.py                 # task 完整性校验（原 verify_task.py）
│   └── metrics.py               # Integration Gap 计算
│
├── scripts/                      # [工具] 一次性或辅助脚本
│   ├── pack_for_publish.py       # dev → public 格式转换
│   ├── compute_gap.py            # 批量 gap 分析
│   └── audit_spec_test.py        # spec↔oracle 一致性检查
│
├── skills/                       # [流水线定义] 各阶段 SKILL.md
│   ├── task-synthesizer/
│   ├── candidate-selector/
│   ├── spec-writer/
│   ├── test-filter/
│   └── task-judge/
│
├── repo-pool/                    # [外部依赖] 上游仓库克隆（gitignore，不提交）
│
├── docs/                         # [文档]
│   ├── TASK_DESIGN.md            # task 设计原则
│   ├── METRIC_DEFINITION.md      # 指标定义
│   ├── RESTRUCTURE_PLAN.md       # 本重构计划
│   └── TASK_REVIEW_ACTION_PLAN.md
│
├── archive/                      # [归档] 旧版本、淘汰的 task
│   ├── superseded-tasks/         # SUPERSEDED 的 task 目录
│   ├── deprecated-skills/        # 旧流水线 SKILL
│   └── old-runs/                 # 早期不规范的评测记录
│
├── .envs/                        # [运行时] 评分虚拟环境（gitignore）
├── .tmp/                         # [运行时] 临时文件（gitignore）
│
├── README.md                     # 项目说明
├── CANDIDATES.md                 # 候选库选择/退休记录
├── .gitignore                    # 忽略 .envs/, .tmp/, repo-pool/, *.pyc
└── pyproject.toml                # harness 的依赖声明
```

---

## 与当前结构的差异

| 变更 | 说明 | 为什么 |
|------|------|--------|
| `tasks/{id}/` 新增 `oracle/tests.py` | 测试代码从 wip 复制到 task 目录 | 不再需要跨目录找测试文件 |
| `tasks/{id}/` 新增 `task.json` | 合并 MANIFEST + taxonomy + kept_nodeids | 一个文件搞定所有元数据 |
| `tasks/{id}/` 新增 `CHANGELOG.md` | 记录 spec 版本、oracle 变更、审计历史 | 解决追溯问题 |
| `candidate-runs/` → `runs/` | 改名更短 + 内部结构标准化 | `prompt.md` 替代 `task_prompt.txt` |
| 根目录垃圾文件 | 全部删除或归入子目录 | 根目录只留 4 个文件 |
| `REPO_POOL.md`, `weakness_table.md` 等 | 移入 `docs/` | 减少根目录文件 |
| `tmp/` + `.tmp/` + `logs/` + `Microsoft/` | 合并为 `.tmp/`，其余删 | 清理 |
| SUPERSEDED task 目录 | 移入 `archive/superseded-tasks/` | tasks/ 只有活跃 task |
| `tools/`, `analysis/`, `results/` | 合并入 `scripts/` 和 `runs/` | 减少顶层目录数 |

---

## task.json 格式（替代 MANIFEST + taxonomy + kept_nodeids）

```json
{
  "instance_id": "httpcore-transport-fullrepro-001",
  "status": "QUALIFIED",
  "repo": "encode/httpcore",
  "repo_commit": "abc123",
  "spec_version": "v2",
  "oracle": {
    "source": "generated_only",
    "test_file": "oracle/tests.py",
    "count": 64,
    "scorer_isolation": ["--remove-path", "httpcore"]
  },
  "taxonomy": {
    "test_pool_request_returns_status_headers_content_and_extensions": "integration",
    "test_url_from_string_exposes_components_and_default_origin_port": "atomic"
  },
  "dependency_map": {
    "test_pool_request_returns_...": ["test_url_from_string_...", "test_request_rejects_..."]
  },
  "stats": {
    "atomic": 15,
    "integration": 35,
    "system_e2e": 14
  },
  "reference_pass_rate": 1.0,
  "tier": "tier1",
  "runs": [
    {
      "run_id": "codex-httpcore-specv1-20260704-001",
      "model": "codex",
      "spec_version": "v1",
      "date": "2026-07-04",
      "passed": 58,
      "total": 64
    }
  ],
  "changelog": [
    "2026-07-04: spec_v1 → spec_v2 (TLS section expanded)",
    "2026-07-12: P1 spec cleanup (removed middleware stack layer description)",
    "2026-07-13: Integration Gap audited (6/6 SPEC ADEQUATE)"
  ]
}
```

---

## CHANGELOG.md 示例

```markdown
# httpcore-transport-fullrepro-001 Changelog

## 2026-07-13
- Integration Gap audit: 6/6 True Gap Events verified as SPEC ADEQUATE
- boltons test_ior removed from oracle (spec deficiency, Python 3.8 |= not documented)

## 2026-07-12
- P1 spec cleanup: removed internal middleware stack layer descriptions
- spec↔oracle consistency audit: CLEAN (no orphaned tests)

## 2026-07-04
- Candidate evaluation: codex-httpcore-specv1-20260704-001 scored 58/64
- Reference gate: 64/64 passed on WSL
- Task-judge verdict: QUALIFIED

## 2026-07-03
- spec_v2 written (expanded TLS and retry sections)
- Track B generated 64 tests, dummy gate passed, reference gate 100%

## 2026-07-01
- spec_v1 written from encode/httpcore source
- Candidate selected from repo-pool
```

---

## 迁移步骤

### Phase 1：根目录清理（5 分钟，无风险）
1. 删除垃圾文件（`=0.16`、shell 残留等）
2. 移动散落文档到 `docs/`
3. 移动散落脚本到 `scripts/`

### Phase 2：tasks/ 结构升级（每个 task 约 2 分钟，脚本化）
1. 对每个活跃 task：
   - 从 `wip/{id}/filter/` 复制 `generated_tests.py` → `tasks/{id}/oracle/tests.py`
   - 合并 `MANIFEST.json` + `taxonomy.jsonl` + `kept_nodeids.txt` → `task.json`
   - 生成 `CHANGELOG.md`（从 wip/PIPELINE_STATE.md 提取历史）
2. 删除 `tasks/{id}/` 下的旧散文件（taxonomy.jsonl、kept_nodeids.txt、MANIFEST.json、spec_test_map.md、reference_score.json、score_result.json、diagnosis_report.md）

### Phase 3：runs/ 标准化（脚本化）
1. `candidate-runs/` → `runs/`
2. 每个 run 内：`task_prompt.txt` → `prompt.md`，确保有 `meta.json`

### Phase 4：archive 归档（5 分钟）
1. 移动 6 个 SUPERSEDED task 到 `archive/superseded-tasks/`
2. 移动 apscheduler（SATURATED）到 `archive/`
3. 清理 `tmp/`、`logs/`、`Microsoft/`

### Phase 5：harness 重命名（2 分钟）
1. `score_pytest_original.py` → `scorer.py`
2. `run.py` → `runner.py`
3. `verify_task.py` → `verify.py`
4. 更新 skills/ 中对旧文件名的引用

---

## 风险控制

- **Phase 2 动 tasks/ 结构**：正在跑的 codex 评测用的是 `wip/` 路径，不受影响
- **Phase 3 动 candidate-runs/**：只改目录名，内容不变
- **Phase 5 动 harness/**：需要同时更新 skills/ 中的引用
- **回滚**：用 git 分支，先 commit 当前状态再操作
