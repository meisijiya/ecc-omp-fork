# ADR-0013: 仓库与运行名改叫 omp-skill-forge / forge-，取代 ecc-omp-

**Date**: 2026-11-03
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

`ecc-omp-` 这个前缀是只收录一个上游时的产物：仓库叫 `ecc-omp-fork`，运行名是
`ecc-omp-<upstream>`，读起来就是「ECC 的 omp 端口」。现在池子里已经有三个上游
（ECC 的 `pool/`、pstack 与 addyosmani 的 `absorbed/`，再加刚收纳的 qa-skills），
名字对内容说了谎：`ecc-omp-correct` 与 ECC 没有关系，`ecc-omp-statechart` 也是。

前缀是公开接口：它出现在系统提示的技能列表里、`skill://` URI 里、agent 名里、
安装根路径里、`omp plugin list` 的插件 id 里。改得越晚，用户侧与文档里的旧名越多。

## Decision

1. **仓库与插件 id** 改成 `omp-skill-forge`：GitHub 仓库名、插件 id、`package.json` 的
   `name`、安装根 `~/.omp/agent/local/omp-skill-forge`、`tools/deploy.py` 与
   `tools/check_plugin_isolation.py` 里的常量同源。远端改名用 `gh repo rename`
   执行一次，随后 `origin` 与文档里的 URL 一并指向新名。
2. **运行名前缀** 改成 `forge-`，仍只落在物化层：`pool/` 与 `manifest/groups.json`
   保留上游名，`tools/refscan.py` 的 `RUNTIME_PREFIX` 是唯一常量，物化、引用改写、
   收纳池重命名、门禁判定都读它。`absorbed_fixups.py` 的批量规则用 `{prefix}`
   占位，前缀再变时只改一处常量并重跑网关。
3. **自有资产目录改名**：`own/skills/ecc-omp-*` → `own/skills/forge-*`；三条运维 skill
   与选路表的名字同样带新前缀，因为自有资产的名字本就按运行名书写。
4. **文档与门禁同步**：`README.md`、`NOTICE.md`、`docs/CATALOG.md`、`docs/agents/*`、
   `own/rules/*`、`own/skills/*` 全部改写；`docs/adr/0007`、`0009`、`0010` 里描述当时
   前缀的历史段落保持原样（ADR 是当时的决定记录，不是现状说明书）。

## Alternatives

- **保留 `ecc-omp-`**：改名要触碰 1,100 余处文本与安装路径，收益只是可读性。否决理由
  是误导性：收纳资产用 ECC 的名字会让用户以为引用的是 ECC 的实现。
- **按来源分前缀**（`ecc-`、`ps-`、`qa-`）：区分来源更精确，但前缀一变就要记名字来源，
  且同一类资产名在不同来源下不可预测；一个前缀更省心，来源由 `manifest/` 记录。

## Consequences

- 旧运行名不再存在：先前装过 `ecc-omp-*` 的环境需要重跑 `tools/deploy.py` 并
  `omp plugin rm` 掉旧插件 id，否则两份资产并存。`tools/deploy.py` 只清理新名下自己的
  安装根，不替用户删旧目录。
- 系统提示里的旧名字消失、新名字出现，`~/.omp/agent/skill-descriptions.db` 里会留下
  旧键的历史行；按 README 的差值法判定启用性，不受影响。
- 前缀长度 6 字符（含连字符），比原来的 8 字符省约 25% 的名称开销：`full` 从 1,168
  降到 876，`java-python` 从 656 降到 492。
