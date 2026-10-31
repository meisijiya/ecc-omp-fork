---
description: 在 omp 中委派子代理的规则——agent 名、并发、结果回收，以及何时不该委派
globs: ["**/*"]
---

# 委派与并行（fork 专属）

## 本 fork 的 agent 清单（带前缀的裸名）

| 用途 | Agent |
| --- | --- |
| 注释质量 | `ecc-omp-comment-analyzer` |
| 静默失败排查 | `ecc-omp-silent-failure-hunter` |
| 类型设计评估 | `ecc-omp-type-design-analyzer` |
| 代码简化 | `ecc-omp-code-simplifier` |
| 死代码清理 | `ecc-omp-refactor-cleaner` |
| 系统设计 | `ecc-omp-architect` |
| 构建报错修复 | `ecc-omp-build-error-resolver` |
| 性能优化 | `ecc-omp-performance-optimizer` |
| 端到端测试 | `ecc-omp-e2e-runner` |
| Java / Kotlin | `ecc-omp-java-reviewer` `ecc-omp-java-build-resolver` `ecc-omp-kotlin-reviewer` `ecc-omp-kotlin-build-resolver` |
| Python | `ecc-omp-python-reviewer` `ecc-omp-django-reviewer` `ecc-omp-django-build-resolver` `ecc-omp-fastapi-reviewer` |
| 数据 / 网络 / 运维 | `ecc-omp-database-reviewer` `ecc-omp-network-architect` `ecc-omp-network-config-reviewer` `ecc-omp-network-troubleshooter` `ecc-omp-homelab-architect` |

omp 自带的通用 agent（`scout`、`reviewer`、`task`、`sonic` 等）不在此表：
通用代码评审、提交信息、需求拆解、探索、TDD 指导这些职能由那些 agent 与其它插件的 skill 承担，
本 fork 不再重复提供。
一点例外：

- 本 fork 的 agent 名一律带 `ecc-omp-` 前缀（如 `ecc-omp-java-reviewer`），
  因此与 omp 内置的 agent 不重名：派子代理时用带前缀的那个。
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
