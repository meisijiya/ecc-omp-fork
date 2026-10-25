# ADR-0007: 运行名带 `ecc-omp-` 前缀，只用于区分

**Date**: 2026-10-25
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

本 fork 把上游 ECC 的编程子集暴露成 omp 插件。上游资产名（`api-design`、`plan`、
`code-reviewer`）是通用词，与 omp 内建资产、别的 omp 插件提供的资产可能同名。本 fork
自己的资产只有一个带前缀（`ecc-omp-router`），其余全裸名，于是：

- 模型看到 `security-reviewer` 时分不清是本仓的 agent 还是 omp 内建的那个；
- 本仓的 command `code-review` 与别的插件提供的 skill `code-review` 同名，
  `skill://code-review` 到底解析到谁取决于运行时状态；
- 用户要求本插件的 skill / command / agent 都能被直接寻址，且名字能一眼看出属于谁。

前缀必须只落在**运行树**这一层：`pool/` 是上游快照（只有 `tools/sync_upstream.py` 能写，
`check_upstream_pin.py` 校验摘要），`manifest/groups.json` 的成员必须与 pool 完全一致，
两者都保留上游原名。

## Decision

上游名 → 运行名的映射是 `ecc-omp-` + 上游名，作用在 skills / commands / agents 三类上；
rules 与 fork 自有资产（`ecc-omp-router`、5 条 rules）不改名——它们不是上游派生，且
`rule://` 是独立命名空间。

映射只实现一处，在 `tools/refscan.py`：

- 判定同时接受上游拼写与运行拼写，判存在用上游名，输出规范形式用运行名；
- 同一个 kind 里两个上游名映射到同一运行名，或与 fork 自有资产名冲突时，**硬失败**
  （`SystemExit`），不静默择一；
- 外部资产（`manifest/external_refs.json` 声明的、由别的插件提供的同名资产）**不加前缀**，
  仍用它们自己的名字；本 fork 自己的同名 command 叫 `ecc-omp-code-review`，
  两者因此不再同名。

物化器把上游名落成运行名（目录名 / 文件名 / frontmatter `name`），并把正文里指向这些
资产的引用一并改写成运行名。散文里不是资产引用的普通词不动。

## Alternatives Considered

### Alternative 1: 统一用裸 `ecc-` 前缀

- **Pros**: 名字更短，与 fork 名 `ecc-omp-fork` 的关系一眼可见。
- **Cons**: 上游 marketplace 已经用裸 `ecc-` 占了一批名字（`ecc-guide`、`ecc-recipes`、
  `ecc-tools-cost-audit`），pool 里也有 `ecc-council`；用裸 `ecc-` 会再造一批重名，
  与「前缀是为了区分」的目的自相矛盾。
- **Why not**: 目的就是消除同名，`ecc-omp-` 与全市场零交集。

### Alternative 2: 给 fork 自有资产也加「已带前缀则跳过」的特殊处理

- **Pros**: `ecc-council` 这类上游名不会变成 `ecc-omp-ecc-council`。
- **Cons**: 映射不再单射，「上游名 ↔ 运行名」要靠一堆条件判断反查，判定与改写两处
  都要复制这套条件；同 kind 内一旦出现两个映射到同一运行名的上游名，会被静默吞掉。
- **Why not**: 保留单射 + 冲突硬失败，映射才能双向反查，判定与改写才不会漂移。

### Alternative 3: 只改目录名，不改 frontmatter `name`

- **Pros**: 改动面小。
- **Cons**: 违反 INV-07（skill `name` 必须等于目录名）与 INV-10（agent `name` 必须等于
  文件名）；omp 读到的资产名与目录名不一致，用户按提示里的名字找不到文件。
- **Why not**: 名字必须处处一致，否则「区分」只做了一半。

## Consequences

### Positive

- 本仓资产与 omp 内建资产、其它插件资产不再同名，模型按名字寻址时归属明确。
- `docs/CATALOG.md` 同时给出运行名与上游名，回溯上游来源不丢信息。
- 上游同步仍然只动 `pool/`；改名全部发生在物化层，`check_upstream_pin.py` 的摘要口径不变。

### Negative

- 资产名变长，提示行里的 skill 名占用的字符数增加（每轮提示开销相应上升）。
- `omp` 全局设置里的 `includeSkills` 之类按名字写的模式需要跟着改前缀。
- fork 自有目录（`own/skills/`、`own/rules/`）不经过引用修复流程，其中的名字要手工维护。

### Risks

- 上游旧拼写若残留在运行树里，模型按旧名读不到资产。`check_refs.py` 把这种引用判为
  缺陷（`upstream spelling of a renamed …`），但判定本身是启发式的：散文里的普通词
  （例如不带反引号的 `plan`）不会被改写，也不会被判成缺陷。
