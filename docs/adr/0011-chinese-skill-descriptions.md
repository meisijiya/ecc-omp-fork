# ADR-0011: skill 的提示行描述改成中文，靠一张触发描述表维护

**Date**: 2026-11-02
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

omp 决定要不要读某个 skill，看的是系统提示里那一行：名字加 description。描述是英文的，
用户用中文提问时，两边对不上。用户按提示词让模型去用对应 skill，模型却经常读的是
最像的那一条英文描述，或者干脆只读索引就自己开写。

改描述有三处硬约束：

1. `pool/` 必须与上游 pin 逐字节一致（ADR-0004），直接改上游文本会让 `check_upstream_pin`
   变红，也让逐条比对上游变更失去意义。
2. 描述是提示行，每轮都付钱。上游英文描述平均两三百字符，73 条 skill 的 java-python
   profile 因此占掉约 4.7K token。
3. 描述要短、要贴中文口语，还要守去 AI 味的写法规则：不用翻案腔，不用提示语冒号，
   顿号不过密，同一段里不连着说同样句式。

## Decision

1. **中文触发描述放一张表**：`manifest/skill_descriptions.zh.json`，138 条
   （132 条上游 + 6 条收纳）。`pool/` 不动，`tools/apply_selection.py` 在物化时把中文
   描述写进运行树的 frontmatter，`name` 仍按 ADR-0007 加 `forge-` 前缀。
2. **描述规范**：两句。第一句说做什么，第二句说什么时候用并带 2 到 4 个中文触发词。
   提示行成本不超过 45 token（汉字按 1 token，其余字符按三分之一 token 估）。
   不用冒号，顿号最多一处，不用「不是…而是」这类翻案腔，不用赋能、闭环、抓手这类词，
   也不出现别的 harness 的名字（INV-02、INV-03、INV-15）。
3. **缺条目即失败**：`apply_selection.py` 遇到没有中文描述的 skill 直接退出；
   `tools/check_zh_descriptions.py` 另外校验覆盖面、写法与自有 skill 的中文描述，
   并接入 CI（`check_absorbed` 之后一步）。
4. **router 同时改**：`own/skills/forge-router/SKILL.md` 的 description 加上触发标记与
   否定边界（什么时候该读、什么时候不用读），正文新增「按用户的话找 skill」四张分主题
   表，把中文说法直接映射到 skill 与 agent；结尾保留「读完就 read 对应 skill」的指令。
   `own/rules/fork-workflow.md` 的 description 与正文都写明开工前先读 router。
5. **正文不翻译**：skill 正文的英文保持原样，只有提示行那一行是中文。

## Alternatives

- **直接改 `pool/` 里的 description**：破坏池摘要门禁，也让上游比对失去基线。
- **只把 router 索引做全**：模型仍可能直接命中某条英文描述而不读索引，索引只是兜底。
- **给每条 skill 另写中文 README**：成本高，且收益落在描述那一行，而不是正文。

## Consequences

- 提示行变便宜：java-python 从约 5.2K token 降到约 3.0K，full 从约 9.8K 降到约 5.5K，
  lite 从约 3.1K 降到约 1.7K。省下的量随 profile 变化。
- 中文提示词更容易命中对应 skill。命中率的真实提升需要跑真实会话采样，本 fork 没有
  这项数据，只保证描述覆盖了全部 skill 且带了触发词。
- 描述内容变成 fork 自有资产，改上游时不必改表；上游新增 skill 会让
  `check_zh_descriptions.py` 直接报缺条目，逼着补上。
- agent 的描述仍是英文。`task` 工具按 agent 的描述选人，这条路径的触发问题没有解决，
  留作后续项。
- `own/skills/` 下的 skill 没有单独的 README，`validate_skill.py` 因此报一条
  `readme.boundary-missing`。本 fork 用仓根 README 与 `docs/CATALOG.md` 覆盖这件事，
  保持四个自有 skill 结构一致，这条警告按取舍接受。
