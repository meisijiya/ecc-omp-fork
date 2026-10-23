---
description: 本 fork 的默认开发流程——先查再写、先计划再实现、验证后再声明完成
globs: ["**/*"]
---

# 开发流程（fork 专属）

上游 ECC 的 `development-workflow` 假设 MCP 工具（Context7 / Exa）、`gh search repos/code`
命令行以及 PRD / architecture / system_design / tech_doc / task_list 等规划文档产物；
上游的 hook 假设写在另一个文件里，本 fork 不携带上游 rules 目录。
本 fork 在 omp 中的等价流程如下。

## 0. 先查再写

写任何新实现之前：

1. 在仓库里搜同类实现（`grep` / `glob`），确认是否已有可复用的模式。
2. 查依赖库是否已经存在，不要手写轮子（`grep` 依赖清单里的名字）。
3. 需要外部资料时先看仓库里已有的文档与注释，再查上游官方文档。

## 1. 先计划再实现

改动跨多个文件、涉及架构决策、或需求本身含糊时，先产出计划再动手：

- 命令：`/plan`（重述需求 + 风险 + 步骤），`/plan-prd`（问题优先的精简 PRD）。
- agent：`planner`（实施计划）、`architect`（系统设计）、`code-architect`（特性架构）。
- 产出计划后等用户确认，不要边猜边改。

改动是单点、机械性的（改个文案、加个分支、换常量），跳过计划直接做。

## 2. 实现

- 动手前先读目标文件，读到真实内容再改。
- 改动尽量小而完整：不要留下半成品状态。
- 新增行为先写测试（见 `fork-verification` 规则）。

## 3. 验证

按 `fork-verification` 规则验证：改完必须跑一遍受影响的东西，
并把**实际输出**贴出来。没跑过就说没跑过。

## 4. 收尾

- 提交信息用 `commit-reviewer` agent 或 `/prp-commit` 生成，遵循 Conventional Commits。
- 更新文档：用 `/update-docs` 命令。
- 清理：确认没有遗留的临时文件、调试输出、被注释掉的死代码。

## 与 skill / command / agent 的分工

- **skill** 是知识（怎么做对），按需 `read skill://<name>`。
- **command** 是流程入口（`/plan`、`/code-review`、`/test-coverage`），直接当命令用。
- **agent** 是并行子任务（评审、探索、修复），用 `task` 派，agent 名用裸名。

三者配合使用，不要只用一个。委派纪律见 `omp-delegation` 规则。
