# ADR-0008: 不发布命令，与其它插件重复的 skill 与 agent 一律不物化

**Date**: 2026-10-28
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

本 fork 的运行树最初包含四类资产（skill / command / agent / rule），其中：

- 24 个上游 command 是流程入口（`plan`、`code-review`、`prp-commit`、`update-docs` 等）；
- 4 个 skill 与 `mattpocock-skills-zh`（devcxl/mattpocock-skills-zh）语义重叠：
  `tdd-workflow`（↔ `tdd`）、`architecture-decision-records` 与 `context-and-decisions`
  （↔ `domain-modeling`）、`intent-driven-development`（↔ `to-spec`）；
- 9 个 agent 与 omp 内建 agent 或其它插件提供的 skill 重叠：
  `code-reviewer`、`security-reviewer`、`commit-reviewer`、`pr-test-analyzer`、
  `code-explorer`、`planner`、`code-architect`、`tdd-guide`、`spec-miner`。

同时，本机 omp 已经装了多个提供同类能力的插件：mattpocock-skills（38 个 skill）、
magpie 用户级 skill 集（40 个）、playwright、karpathy-guidelines。
它们已覆盖通用评审、TDD、规格拆解、探索、提交信息这几类职能。

结果是同一件事有两个入口：模型面对「做代码评审」这类请求时，既可能派 `ecc-omp-code-reviewer`，
也可能读 mattpocock 的 `code-review` skill。命名区分（ADR-0007）解决的是「找得到哪个名字」，
解决不了「该用哪个」——重复的能力各自被注入提示行，token 双倍花，行为还不一致。

用户侧的使用习惯也是决定因素：命令用得少，skill 已经够用。

## Decision

1. **本 fork 不发布命令。** 三个 profile 的 `commands.groups` 全部为空；
   上游的 24 个 command 快照只保留在 `pool/` 里（供回溯与日后恢复），不物化。
   `package.json` 去掉 `pi.prompts` 声明，`tools/deploy.py` 在安装根清理旧的 `commands/` 目录。
2. **与其它插件重叠的 skill 与 agent 一律不物化**，判定口径是「这个能力在本机已经有人提供」，
   而不是「上游有没有这个文件」。重叠清单写进各 profile 的 `exclude`。
3. **`pool/` 里的上游快照一个不动。** 去重是 profile 层的选择，不是删上游内容——
   `manifest/groups.json` 的成员必须与 `pool/` 完全一致（`check_upstream_pin.py` 校验摘要）。

被裁掉的能力由谁接管：

| 裁掉的资产 | 接管方 |
| --- | --- |
| 24 个 command | 无（流程改由 skill + agent 组合承担） |
| `tdd-workflow` | mattpocock `tdd`；各语言 TDD skill 仍在本 fork |
| `architecture-decision-records` / `context-and-decisions` | mattpocock `domain-modeling` |
| `intent-driven-development` | mattpocock `to-spec` |
| `code-reviewer` / `security-reviewer` | omp 内建 `reviewer` / `security-reviewer`，本 fork `security-review` skill |
| `commit-reviewer` | 本 fork `conventional-commit-review` skill |
| `pr-test-analyzer` | 本 fork `test-collaboration` skill |
| `code-explorer` | omp 内建 `scout`，本 fork `codebase-onboarding` skill |
| `planner` / `code-architect` | mattpocock `wayfinder` / `codebase-design` |
| `tdd-guide` | mattpocock `tdd` |
| `spec-miner` | mattpocock `to-spec` |

## Alternatives Considered

### Alternative 1: 保留命令，只删重叠的 skill 与 agent

- **Pros**: `/ecc-omp-plan` 这类入口比「读 skill 再派 agent」少一步。
- **Cons**: 命令与 skill 大量指向同一件事（`/ecc-omp-code-review` 与 `code-review` skill、
  `/ecc-omp-test-coverage` 与各语言测试 skill），保留命令等于保留第二套流程入口；
  用户明确表示命令用得少。
- **Why not**: 保留一套用得少的入口，代价是每轮多 24 条命令广告与两套心智模型。

### Alternative 2: 只按「上游有没有」判重，不看本机实际有什么

- **Pros**: 判定纯在本仓内完成，不依赖本机装了哪些插件，CI 可复现。
- **Cons**: 上游 71 个 agent、132 个 skill 几乎覆盖了所有通用工程职能，按「上游自足」判重等于什么都不删。
- **Why not**: 去重的目的就是减少重复暴露，不能把「本机已有人提供」这个事实排除在判据外。

### Alternative 3: 删 `pool/` 里的上游快照，让上游不再提供这些能力

- **Pros**: 彻底断掉重复能力的来源。
- **Cons**: `pool/` 是上游快照，由 `tools/sync_upstream.py` 单写，`check_upstream_pin.py` 按摘要校验；
  改它会破坏 pin 一致性，也让日后恢复某个能力没有依据。
- **Why not**: 快照是事实，不是配置；要改的是「发布什么」，不是「上游有什么」。

## Consequences

### Positive

- 每轮提示里不再有重复能力的多个入口，行为更一致。
- `java-python` profile 的注入量从 ~5.1K token 降到 ~4.6K（skill 描述 + 运行名口径）。
- 命令相关的悬空引用一次性清零：`own/` 里的选路表与流程规则不再点名已删除的命令。

### Negative

- 习惯了 `/ecc-omp-plan` 这类入口的用户要改成「派 agent」或「读 skill」。
- 上述能力依赖本机其它插件在场。卸载 mattpocock 会让对应能力消失，
  而本 fork 不会补上。

### Risks

- 判据依赖本机插件集合。插件清单变了，「重复」的定义就变了；
  这也是本 fork 把去重写在 profile 层（可随时改）而不是写进代码里的原因。
- `own/` 里的选路表与委派规则手写了运行名，不参与引用改写流程，资产增删时要手工同步，
  否则会出现指向已删资产的悬空引用（由 `check_refs.py` 兜住）。
