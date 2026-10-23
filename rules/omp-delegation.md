---
description: 在 omp 中委派子代理的规则——agent 名、并发、结果回收，以及何时不该委派
globs: ["**/*"]
---

# 委派与并行（fork 专属）

## 本 fork 的 agent 清单（裸名）

| 用途 | Agent |
| --- | --- |
| 通用代码评审 | `code-reviewer` |
| 提交信息 | `commit-reviewer` |
| PR 测试覆盖审查 | `pr-test-analyzer` |
| 注释质量 | `comment-analyzer` |
| 静默失败排查 | `silent-failure-hunter` |
| 类型设计评估 | `type-design-analyzer` |
| 安全审查 | `security-reviewer` |
| 代码简化 | `code-simplifier` |
| 死代码清理 | `refactor-cleaner` |
| 系统设计 | `architect` |
| 特性架构 | `code-architect` |
| 代码库探索 | `code-explorer` |
| 实施计划 | `planner` |
| 构建报错修复 | `build-error-resolver` |
| 性能优化 | `performance-optimizer` |
| TDD 指导 | `tdd-guide` |
| 端到端测试 | `e2e-runner` |
| 规格提取 | `spec-miner` |
| Java / Kotlin | `java-reviewer` `java-build-resolver` `kotlin-reviewer` `kotlin-build-resolver` |
| Python | `python-reviewer` `django-reviewer` `django-build-resolver` `fastapi-reviewer` |
| 数据 / 网络 / 运维 | `database-reviewer` `network-architect` `network-config-reviewer` `network-troubleshooter` `homelab-architect` |

omp 自带的通用 agent（`scout` `reviewer` `security-reviewer` `task` `sonic`）不在此表。
两点例外：

- 本 fork 自带同名 `security-reviewer`，它会**遮蔽** omp 内置的那个（本 fork 版本优先）。
- `seance` 是 omp 自带的会话回溯 agent，**不是始终可用**：它只在可生成时才会被列出，
  plan 模式下会被隐藏，而且必须额外提供 `sourceSession` 等专属参数。

## 何时委派

**适合委派**：独立子任务、可并行的多份工作、需要只查证的陌生代码库。
**不适合委派**：单文件小改、需要当前对话上下文的连续决策、用户只问一句话。

## 委派纪律

1. **一次派一组，别一个一个派**。相互独立的子任务应在同一次 `task` 调用中并行。
   用 `task.batch` 的批量形态时，必须提供非空的共享 `context`，
   每个条目还要写清自己的 `solutionSpace`。
2. **子代理拿到的上下文有限**。必须写清：目标文件、非目标、具体步骤、验收标准。
   不要假设它看过本对话。
3. **验收看原始输出**，不要照单全收子代理的结论。子代理说「已修复」不等于真的修好。
4. **子代理再派子代理会撞上限**。递归深度由 `task.maxRecursionDepth` 控制（默认 2），
   agent frontmatter 的 `spawns` 只声明「这个 agent 允许派哪些 agent」，不是深度开关。
   需要更深分解时由主代理自己展开，不要让子代理链式套娃。
5. **别把推理外包给只读代理**。`scout` 一类只读代理适合找信息，不适合替它做判断。
