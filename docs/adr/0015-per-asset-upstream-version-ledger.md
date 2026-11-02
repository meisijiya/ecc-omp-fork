# ADR-0015: 逐资产的版本台账按内容寻址，同步必须经过物化链路

**Date**: 2026-11-03
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

`manifest/upstream.json` 的 pin 只说「`pool/` 对应上游哪个 commit」，说不了三件事：

1. **哪几条**资产变了。上游一次提交动一个 skill 与动二十个 skill，pin 层面看起来一样。
2. **收纳来源**如何核对。`absorbed/` 有三个来源、各自一个 commit，pin 只有 ECC 一个。
3. **我手上的副本是不是那个 commit 的样子**。收纳副本经过声明式改写，与上游同路径文件
   不再逐字节相等，光比对 commit 说明不了改写是否仍然成立。

上游本身没有可用的逐资产版本：ECC 的 `pi/core/skills/` 全量 grep `^version:` 命中 0 处；
qa-skills 每条 frontmatter 有 `version: 0.9.0`，但作者不保证随每次改动递增。拿版本号当
检测信号会漏更新。

另一条约束来自 ADR-0001：上游文本的改写只发生在物化层。所以「同步」不能是
`git pull` 把上游文件搬进运行树，只能是「刷新源副本（`pool/` 或 `absorbed/`）→ 重放
改写规则 → 重新物化 → 跑门禁」。

## Decision

1. **版本 = 内容**。`manifest/asset_versions.json` 为每个来自上游的资产记 git tree oid
   （目录内容哈希）与能读到的上游 `version:`（读不到就是 null）。tree oid 随内容变，
   不看版本号，也不看 commit。
2. **资产清单不另立一份**。ECC 侧取 `manifest/groups.json` 的 `skills`（路径
   `pi/core/skills/<name>`）与 `agents`（`agents/<name>.md`），收纳侧取
   `manifest/absorbed.json` 的 `skills[*].path`。台账只记「当前 record 时的 oid」，
   清单变了就 `record` 重写，避免维护第二份名单。
3. **`tree` 允许为 null**：`forge-engineering-principles` 是本地把 8 份 principle 快照
   拼成的生成物，上游没有对应目录。`check` 对 null 视为「无需比对」，不当漂移。
4. **CLI**：`tools/upstream_versions.py` 提供 `record`（拉取 → 计算 → 写台账）、
   `check`（联网逐条比对，有漂移退出 1）、`check --offline`（不联网，只校验台账形状与
   覆盖，CI 跑这条）、`show`（离线打印台账）。退出码 0 / 1 / 2 = 通过 / 有缺陷 /
   输入不可读。
5. **拉取与缓存**：克隆缓存放 `.upstream-cache/<slug>`（进 `.gitignore`），复用已有克隆，
   git 调用一律 `-c http.version=HTTP/1.1`（该网络 HTTP/2 会断流）。
6. **漂移之后走对应链路**，不许裸拉：ECC 侧 `sync_upstream.py`（刷 `pool/` 与 pin）→
   `apply_selection.py`；收纳侧 `sync_absorbed.py`（重放 `absorbed_fixups.py` 的规则）。
   `SOURCE_RULES` 的命中总数与 EXISTS 判定让「上游改写法但规则没跟上」变成失败而不是静默。

## Alternatives

- **只用 pin**：一条 commit 说明全部资产，改动定位不了，收纳来源也覆盖不到。
- **用上游 `version:` 字段**：ECC 没有，qa-skills 不可靠，检测会漏。
- **逐文件 sha256**：信息最细，但把 78 个收纳文件与 150 个运行树的摘要再存一遍，
  与 `check_absorbed.py` 重复，且人对着一屏摘要判断不出「哪条 skill 更新了」。
- **直接比对改写后的副本与上游文本**：改写规则一变就会全红，噪音掩盖真实更新。

## Consequences

- 台账是快照：`record` 之后上游再动，`check` 才会报；CI 的定时同步任务里跑联网 `check`
  就能每周发现变化，`check --offline` 保证清单与台账不脱节。
- 收录新资产、改 profile、删资产都要重跑 `record`，否则 `check --offline` 会报缺条目。
- oid 变了但改写规则仍成立时，只需要刷新源副本并重新物化；oid 变了且规则不再命中时，
  `sync_absorbed.py` 会以 `Drift` 失败，维护者据此改规则——这与 ADR-0014 里
  `SOURCE_RULES` 的计数校验是同一道闸。
