---
description: omp 的工具体系与 Claude Code 不同——文件读写、搜索、委派、子代理的具体工具名与调用方式
globs: ["**/*"]
---

# omp 工具约定（fork 专属）

本 fork 只在 omp 中运行。上游 ECC 的部分规则文本假设 Claude Code 的工具名，
直接照搬会指向不存在的工具。本文件给出 omp 侧的对应关系。

## 工具对应

| 目的 | Claude Code（ECC 原文假设） | omp |
| --- | --- | --- |
| 读文件 | `Read` | `read` |
| 改文件 | `Edit` / `Write` | `edit`（行锚点补丁）/ `write`（新建或整体覆盖） |
| 搜索文件内容 | `Grep` | `grep`（正则） |
| 找文件 | `Glob` | `glob` |
| 跑命令 | `Bash` | `bash` |
| 委派子代理 | `Task(subagent_type=...)` | `task`，用 `agent` 字段指定 agent 名称 |
| 任务清单 | `TodoWrite` | `todo` |
| 读技能正文 | 读 SKILL.md | `read` 读 `skill://<name>` |
| 读规则正文 | 读 rules/*.md | `read` 读 `rule://<name>` |

## 硬约定

1. **改文件用 `edit` 而不是 `write`**。`edit` 的默认模式是 `hashline`：
   输入是 `[PATH#TAG]` 分节 + 行锚点补丁（`PUT 4.=4:`），一次调用可以带多个分节、
   同时改多个文件。`write` 会整文件覆盖，仅在新建文件或需要整体重写时使用。
2. **改之前先读**。`edit` 的 `[PATH#TAG]` 里的 tag 必须来自最近一次 `read` / `grep` /
   成功的 `edit` 结果里带的四位十六进制 snapshot tag；不能凭记忆构造，
   无 tag 的锚定编辑会被 `hashline` 拒绝。
3. **搜索优先用 `grep` / `glob`**，不要用 `bash` 跑 `grep`/`find`/`ls` 去遍历目录。
4. **委派用 `task`**，并在 `agent` 字段里给出本 fork 存在的 agent 名。
   本 fork 的 agent 名是**裸名**（如 `ecc-omp-java-reviewer`、`ecc-omp-python-reviewer`），
   带本 fork 的 `ecc-omp-` 前缀，但不是 Claude Code 的 `ecc:` 前缀形式。并行就是同一条消息里的多个 `task` 调用；
   用 `task.batch` 的批量形态时必须提供非空的共享 `context`。
5. **不要臆造不存在的工具**。上游 ECC 规则里出现的 `Agent(subagent_type:)`、
   `mcp__playwright__*`、`mcp__context7__*` 在本机不一定可用，
   除非确认对应 MCP server 已连接。

## 技能与规则的按需读取

- 技能正文：`read` 读 `skill://<name>`。本 fork 物化的技能**不带** `hide: true`，
  因此它们会正常出现在系统提示的技能列表里；`hide: true` 的语义也不是「禁用」，
  只是从列表里隐藏，正文仍可通过 `skill://<name>` 读到。
- 规则正文：`read` 读 `rule://<name>`。规则是「按需加载」的知识，
  先看规则列表判断适用性，再决定读哪几条。
