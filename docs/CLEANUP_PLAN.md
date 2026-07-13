# Bmk-dev 目录清理计划

> 原则：不动 pipeline 关键路径（tasks/, wip/, harness/, repo-pool/, skills/, candidate-runs/, .envs/）
> 只清理根目录垃圾和散落文件

---

## 1. 删除根目录垃圾文件

这些是 shell 命令残留或误创建的文件，无任何有用内容：

```
 ;  --version; fi; done
=0.16
=1.4
=1.7.0,
=5.0,
=9
```

## 2. 移动散落文件到正确位置

| 文件 | 目标 | 原因 |
|------|------|------|
| `compute_integration_gap.py` | `scripts/` | 分析脚本 |
| `integration_gap_results.json` | `results/` | 分析产物 |
| `codex_exec_last_message.txt` | 删除 | 调试残留 |
| `last_message_3.txt` | 删除 | 调试残留 |
| `judge_reaudit_20260703.md` | `docs/` | 文档 |
| `MANIFEST.json`（根目录的） | 删除或移入 docs/ | 不应在根目录 |
| `WORKFLOW_CN.md` | `docs/` | 文档 |
| `.coverage` | .gitignore + 删除 | 运行时产物 |
| `.doit.db` | .gitignore + 删除 | 运行时产物 |

## 3. 合并重复目录

- `.tmp/` 和 `tmp/` → 保留 `.tmp/`（harness 用），`tmp/` 内容迁入后删除
- `Microsoft/` → 检查内容后删除（疑似误创建）
- `logs/` → 如果是旧日志则移入 `archive/logs/`

## 4. 更新 .gitignore

追加：
```
.coverage
.doit.db
.tmp/
*.pyc
__pycache__/
.envs/
```

## 5. 根目录最终结构

```
Bmk-dev/
├── .envs/           # 评分虚拟环境（gitignore）
├── .tmp/            # 临时运行目录（gitignore）
├── archive/         # 历史版本、旧数据
├── candidate-runs/  # 候选模型评测记录
├── docs/            # 文档集中管理
├── harness/         # 评分脚本
├── repo-pool/       # 上游仓库克隆
├── results/         # 分析产出（gap 计算等）
├── scripts/         # 工具脚本
├── skills/          # 流水线 SKILL 定义
├── tasks/           # 正式 task（spec + oracle 元数据）
├── tools/           # 辅助工具
├── wip/             # 流水线工作区
├── .gitignore
├── AGENTS.md
├── CANDIDATES.md
├── README.md
├── REPO_POOL.md
└── specbench_rp.html
```

保留在根目录的文件只有：项目级 README/AGENTS/CANDIDATES + 池状态 + 报告页面。
其余全部归入对应子目录。
