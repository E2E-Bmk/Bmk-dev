# Spec2Repo 发布重构计划

> 目标：将当前 Bmk-dev 开发工作区重构为可发布的 GitHub benchmark 仓库结构
> 日期：2026-07-13

---

## 一、目标结构

```
spec2repo-benchmark/
├── README.md
├── LICENSE
├── pyproject.toml
├── harness/
│   ├── __init__.py
│   ├── evaluate.py
│   ├── scorer.py
│   ├── metrics.py
│   └── Dockerfile
├── tasks/
│   └── {task-id}/
│       ├── task.json
│       ├── spec.md
│       └── oracle/
│           ├── tests.py
│           ├── conftest.py (可选)
│           └── requirements.txt
├── results/
│   └── {model-name}/
│       └── {task-id}.json
├── scripts/
│   ├── build_hf_dataset.py
│   ├── run_all.py
│   └── compute_gap.py
└── docs/
    ├── TASK_DESIGN.md
    └── METRIC_DEFINITION.md
```

---

## 二、当前结构 → 目标结构的映射

| 源路径（Bmk-dev/） | 目标路径（spec2repo-benchmark/） | 操作 |
|---|---|---|
| `tasks/{id}/spec.md` | `tasks/{id}/spec.md` | 直接复制 |
| `wip/{id}/filter/generated_tests.py` | `tasks/{id}/oracle/tests.py` | 复制 + 清洗 |
| `wip/{id}/filter/rewritten_upstream_tests.py` | `tasks/{id}/oracle/tests_upstream.py` | 复制 + 清洗（如存在）|
| `wip/{id}/filter/conftest.py` 或相关 fixtures | `tasks/{id}/oracle/conftest.py` | 复制（如存在）|
| `tasks/{id}/taxonomy.jsonl` | 合并入 `tasks/{id}/task.json` 的 taxonomy 字段 | 转换 |
| `tasks/{id}/kept_nodeids.txt` | 合并入 `tasks/{id}/task.json` 的 test_ids 字段 | 转换 |
| `tasks/{id}/MANIFEST.json` | 合并入 `tasks/{id}/task.json` 的 metadata | 提取关键字段 |
| `tasks/{id}/reference_score.json` | `task.json` 的 reference_pass_rate 字段 | 提取数值 |
| `tasks/{id}/score_result.json` | `results/{model}/{id}.json` | 移动 + 标注模型名 |
| `tasks/{id}/diagnosis_report.md` | 不发布 | 留在 dev 工作区 |
| `tasks/{id}/spec_test_map.md` | 不发布 | 留在 dev 工作区 |
| `harness/score_pytest_original.py` | `harness/scorer.py` | 重构为模块 |
| `harness/run.py` | `harness/evaluate.py` | 重构 |
| `skills/` | 不发布 | 内部流水线 |
| `wip/` | 不发布（除了 oracle 测试代码被提取走）| 内部 |
| `repo-pool/` | 不发布 | 太大；README 中标注上游 commit |
| `candidate-runs/` | 不发布（score 提取到 results/）| 内部 |

---

## 三、具体步骤

### 步骤 1：创建目标仓库骨架

```bash
mkdir spec2repo-benchmark
cd spec2repo-benchmark
git init
mkdir -p harness tasks results scripts docs
```

### 步骤 2：编写打包脚本 `scripts/pack_from_dev.py`

该脚本自动从 Bmk-dev 提取数据，生成发布结构：

```python
输入：Bmk-dev/tasks/、Bmk-dev/wip/
输出：spec2repo-benchmark/tasks/{id}/

对每个活跃 task：
1. 复制 spec.md
2. 从 wip/{id}/filter/ 找到测试 .py 文件 → 复制到 oracle/tests.py
   - 去掉绝对路径（sed 替换）
   - 去掉对 wip/ 或 Bmk-dev/ 的引用
   - 验证文件顶部没有 benchmark 内部信息
3. 从 taxonomy.jsonl + kept_nodeids.txt + MANIFEST.json 合成 task.json
4. 从 score_result.json 提取结果到 results/
5. 生成 oracle/requirements.txt（从 wip/{id}/ 的 venv 或手动指定）
```

### 步骤 3：清洗测试代码

对每个 oracle/tests.py 执行：

| 检查项 | 操作 |
|--------|------|
| 绝对路径 `/mnt/g/research/...` | 替换为相对路径或参数化 |
| `sys.path.insert(0, ...)` hack | 移除（scorer 负责设 PYTHONPATH）|
| 引用 `wip/`、`Bmk-dev/` | 移除 |
| 测试文件中的 benchmark 元信息注释 | 移除 |
| import 私有模块 `from pkg._xxx` | 不应存在（已审计）；如有则报错 |
| 硬编码平台路径 | 参数化 |

### 步骤 4：合成 task.json

```python
# 伪代码
task_json = {
    "instance_id": manifest["task_id"],
    "repo": manifest.get("repo", infer_from_id()),
    "repo_commit": manifest.get("commit", ""),
    "language": "python",
    "oracle_count": len(kept_nodeids),
    "test_file": "oracle/tests.py",  # 相对路径
    "scorer_isolation": parse_isolation(manifest),
    "taxonomy": {  # 从 taxonomy.jsonl 转换
        nodeid_to_function_name(k): v["layer"]
        for k, v in taxonomy_entries
    },
    "dependency_map": {},  # 后续补充
    "stats": {
        "atomic": count_atomic,
        "integration": count_integration,
        "system_e2e": count_e2e
    },
    "reference_pass_rate": extract_from_ref_score(),
    "tier": assign_tier(),
    "metadata": {
        "qualified_date": manifest.get("qualified_date"),
        "oracle_source": manifest.get("oracle_source")
    }
}
```

### 步骤 5：重构 harness

| 现有文件 | 重构为 | 关键变更 |
|----------|--------|----------|
| `score_pytest_original.py` | `harness/scorer.py` | 接受 task_dir 参数而非全局路径 |
| 无 | `harness/metrics.py` | Integration Gap 计算（含 dependency_map）|
| 无 | `harness/evaluate.py` | 端到端入口：给模型 spec → 收集输出 → 跑 scorer → 算 metrics |
| 无 | `harness/Dockerfile` | Ubuntu + Python 3.11 + pytest + 必需依赖 |

### 步骤 6：编写文档

| 文件 | 内容 |
|------|------|
| `README.md` | 项目介绍、快速开始、评测命令、引用格式 |
| `docs/TASK_DESIGN.md` | task 设计原则（从审查框架精简）|
| `docs/METRIC_DEFINITION.md` | Integration Gap 公式定义（含 dependency map 精确版）|
| `LICENSE` | Apache 2.0 或 MIT |

### 步骤 7：生成 HuggingFace dataset

```python
# scripts/build_hf_dataset.py
# 遍历 tasks/*/task.json + oracle/tests.py
# 输出 JSONL 格式供 HF datasets 库加载
```

### 步骤 8：验证

```bash
# 对每个 task 做 dry-run 验证
python harness/evaluate.py --task tasks/httpcore-transport-001 --dry-run
# 确认：能找到 spec.md、能加载 tests.py、能运行 pytest、能计算 gap
```

---

## 四、不发布的内容（留在 Bmk-dev）

| 内容 | 原因 |
|------|------|
| `wip/` | 流水线中间产物，审计用 |
| `repo-pool/` | 上游仓库克隆，太大 |
| `candidate-runs/` | 原始评测轨迹 |
| `skills/` | 内部流水线操作手册 |
| `archive/` | 历史版本 |
| `spec_test_map.md` | 内部映射文档 |
| `diagnosis_report.md` | 内部诊断 |
| `CANDIDATES.md` | 选择/退休日志 |
| `weakness_table.md` | 模型弱点追踪 |

---

## 五、工作量估计

| 步骤 | 自动化程度 | 时间 |
|------|-----------|------|
| 1. 骨架 | 全自动 | 5 分钟 |
| 2. 打包脚本 | 需编写 | 1-2 小时 |
| 3. 清洗测试 | 脚本 + 人工审查 | 2-3 小时 |
| 4. task.json 合成 | 全自动（脚本）| 30 分钟 |
| 5. harness 重构 | 需编写 | 3-4 小时 |
| 6. 文档 | 人工 | 2-3 小时 |
| 7. HF dataset | 脚本 | 30 分钟 |
| 8. 验证 | 半自动 | 1-2 小时 |
| **总计** | | **~12-16 小时** |

---

## 六、优先级建议

1. **先写打包脚本**（步骤 2-4），得到干净的 tasks/ 输出
2. **然后重构 harness**（步骤 5），确保能端到端评测
3. **最后写文档**（步骤 6），因为其内容依赖前两步确定的接口

可以在跑 candidate 评测的同时并行做这件事——两者不冲突。
