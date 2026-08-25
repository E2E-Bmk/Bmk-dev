# Worker 任务：Oracle Atomic 测试清理

## 目标

从所有 34 个 task 的 `oracle/test_atomic.py` 中移除违反 Q1 原则的测试——即那些因为绑定了特定模块路径而非测试行为的测试。

清理完成后，剩余的所有 atomic 测试应满足：**任何行为正确但内部组织不同的实现都能通过它。**

## 判断标准

对 `oracle/test_atomic.py` 中的每个测试函数，检查：

**保留** — 如果测试：
- 调用 spec 中明确承诺的公共入口（顶层 import 或 CLI）
- 执行了具体的行为断言（检查返回值、副作用、异常类型）
- 一个换了内部模块组织的正确实现能通过

**移除** — 如果测试：
- 其核心断言就是 `from pkg.submodule import SomeClass` 能成功（import 本身就是测试内容）
- 检查特定子模块路径的存在性（如 `hasattr(pkg, 'utils')`）
- 会因为模型把函数放在不同子模块下而 collection error，即使函数行为完全正确
- 检查原库实现的具体属性/方法签名但 spec 中没有承诺这些

## 怎么判断一个测试是否违反 Q1

快速检验法：**如果模型把这个功能实现在不同的文件/模块路径下（行为完全相同），这条测试会不会因为 ImportError 而挂？**

- 会 → 违反 Q1，移除
- 不会（因为测试从 spec 承诺的顶层路径 import）→ 保留

## 具体执行步骤

对每个 task 目录（`tasks/{task-id}/`）：

1. 读 `oracle/test_atomic.py`
2. 读 `spec.md` 的 "Installable Surface" 或类似段落，确认 spec 承诺了哪些 import 路径
3. 对每个 test 函数：
   - 看它 import 了什么
   - 如果 import 路径在 spec 的 "Installable Surface" 中 → 保留
   - 如果 import 路径不在 spec 中（子模块内部路径）→ 移除
4. 移除的测试同时从 `task.json` 的 `taxonomy` 字段中删除对应 key
5. 更新 `task.json` 的 `stats.atomic` 计数
6. 更新 `task.json` 的 `oracle.count`

## 重点关注的 task（已知有大量假 atomic）

| Task | 问题 | 预计移除数 |
|------|------|-----------|
| cookiecutter-fullrepro-001 | `cookiecutter.utils`、`cookiecutter.prompt`、`cookiecutter.config` 等子模块 import | ~20-30 |
| pelican-sitegen-fullrepro-001 | `pelican.urlwrappers`、`pelican.paginator` 属性测试 | ~5-10 |
| invoke-taskrunner-fullrepro-001 | 部分 Config/Executor 子模块 | ~5-10 |
| jrnl-journal-fullrepro-002 | `jrnl.journals`、`jrnl.plugins` 子模块 | 待查 |

其余 task（如 httpcore、doit、dynaconf、h2 等）大概率没问题——它们的 atomic 测试都通过顶层 import 调用。

## 不要做的

- **不要移除 integration/e2e 测试**——那些本来就通过公开 CLI/API 入口调用，不受影响
- **不要修改 spec.md**
- **不要修改 test_integration.py**
- **不要改变测试的行为逻辑**——只移除整个测试函数，不做改写

## 验收标准

清理完成后：
- 对每个 task 运行 `python -c "import ast; ast.parse(open('oracle/test_atomic.py').read())"` 确认语法正确
- task.json 中的 `stats.atomic` 与 test_atomic.py 中的 `def test_` 函数数量一致
- 不存在任何 atomic 测试的第一行是从 spec 未承诺的子模块路径 import

## 完成后通知

完成后在每个修改过的 task.json 中加一个字段：
```json
"oracle_cleanup_date": "2026-07-14",
"oracle_cleanup_removed": 5
```
