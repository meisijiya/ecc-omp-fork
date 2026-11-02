# ADR-0012: agent 的提示行描述改成中文，复用同一张表机制

**Date**: 2026-11-02
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

omp 的 `task` 工具按 agent 的 name + description 选人。agent 描述仍是英文时，中文
提问同样对不上，模型会挑名字最像的那一个，或者直接自己做。skill 侧已经把提示行
描述改成中文（ADR-0011），agent 侧是同一条触发路径，却没动，是缺口。

约束同 ADR-0011：

1. `pool/` 必须与上游 pin 逐字节一致（ADR-0004），不能直接改上游 agent 文本。
2. 描述是提示行，每轮都付钱，必须短。
3. 写法规则与 skill 侧一致：不用翻案腔，不用提示语冒号，顿号不过密，不出现别的
   harness 的名字。

## Decision

1. **中文触发描述放一张表**：`manifest/agent_descriptions.zh.json`，71 条，键为 agent
   上游名（去掉 `.md` 的文件名），与 `manifest/groups.json["agents"]` 声明的 71 个
   成员一一对应。`pool/` 不动，`tools/apply_selection.py` 的 `materialize_agents`
   在物化时把中文描述写进运行树的 frontmatter，`name` 仍按 ADR-0007 加 `forge-`
   前缀，不改 `name` 行，不改 `tools:` 行。
2. **复用同一套写法门禁**：`tools/check_zh_descriptions.py` 同时管 skill 与 agent，
   覆盖 `manifest/groups.json["agents"]` 里声明的每个 agent；写法规则复用现有的
   `line_cost()` 与 `FORBIDDEN` / `HARNESS` 列表，不复制第二套。agent frontmatter
   里不能出现别的 harness 名字。
3. **缺条目即失败**：`apply_selection.py` 遇到没有中文描述的 agent 直接退出；
   `check_zh_descriptions.py` 缺表时报告「缺表」并以非零退出。
4. **agent 描述与 skill 描述的差别**：agent 描述只管「谁来干这件事」，skill 描述
   管「用哪条流程/知识」；agent 的触发词更偏向角色与任务类型（评审、构建、架构、
   测试），skill 的触发词更偏向动作与领域。字数与写法规则完全相同。
5. **正文不翻译**：agent 正文的英文保持原样，只有提示行那一行是中文。

## Alternatives

- **直接改 `pool/agents/` 里的 description**：破坏池摘要门禁，也让上游比对失去基线。
- **只做 router 索引**：模型仍可能直接命中英文描述而不读索引，索引只是兜底。
- **给 agent 另写一套门禁脚本**：重复维护，且两边写法会漂移。

## Consequences

- agent 提示行变成中文，`task` 工具按 agent 描述选人这条路径的触发问题得到解决。
- 覆盖 71 个 agent（= manifest/groups.json["agents"] 成员数 71，表条数 71，一一
  对应）。三档 profile 物化后的 agent 数与提示行 token（汉字按 1，其余字符按
  1/3.5）：

  | profile | agent 数 | 英文描述 | 中文描述 |
  | --- | --- | --- | --- |
  | full | 49 | 约 2955 | 约 1706 |
  | java-python | 22 | 约 1205 | 约 775 |
  | lite | 11 | 约 627 | 约 374 |

  全表 71 条合计约 2517 token，单条均值约 36，最长 `code-architect` 约 42，
  最短 `go-reviewer` 约 28，都在 45 的上限内。
- 描述内容变成 fork 自有资产，改上游时不必改表；上游新增 agent 会让
  `check_zh_descriptions.py` 直接报缺条目，逼着补上。
- **未验证风险**：agent 描述变中文后 `task` 工具按中文说法选人，命中率未实测。
  目前只保证描述覆盖了全部 71 个 agent、写法合规、提示行更便宜（full profile
  英文约 2955 token → 中文约 1706 token）；真实选人是否更准要跑真实会话采样，
  本 fork 没有这项数据。
