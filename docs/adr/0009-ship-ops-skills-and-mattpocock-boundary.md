# ADR-0009: 以 mattpocock 为重叠基准，ECC fork 补齐发布 / 部署 / 运维能力

**Date**: 2026-11-01
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

ADR-0008 定了两条规则：不再发布命令；与本机其它插件重复的资产不物化。但「重复」当时只按
mattpocock-skills（汉化版 `mattpocock-skills-zh`）与 omp 内建资产判过一次，判据落在
profile 的 `exclude` 列表里。此后暴露两个问题。

**一、判重基准不完整。** 本机还有 magpie 用户级 skill 集（40 条软链到
`~/.config/magpie/library/skills/`），其中 `addyosmani/agent-skills` 贡献的 25 条一条未启用
（全是死链，不占注入量），另有 4 条与 ECC 强重叠且**已启用**：
`automated-e2e-testing`、`code-reviewer`、`writing-springboot-tests`、`spring-boot-team-harness`。
用户明确表态：addyosmani 那个库自己不会启用，**有重叠的以 ECC 为准**；同时
mattpocock 一定会用，**ECC fork 不能与 mattpocock 重叠**。

**二、ECC fork 缺 ship / 部署 / 运维能力。** 上游 `pool/skills/` 的 132 个 skill 里，
运维相关的只有 `deployment-patterns`、`docker-patterns`、`kubernetes-patterns`、
`production-audit`、`dashboard-builder`、`module-regression`、`benchmark` 几个，
且分在 G2（通用工程规范）与 G10（UI 打磨 / 产品 / 协作）里——`dashboard-builder`
这种运维监控面板 skill 落在「非核心编程」组，`java-python` profile 直接选不到它。
上游还**没有**可观测性（指标 / SLO / 告警）、事故响应（定级 / 止血 / 复盘）、
发布管理（tag / changelog / 分级发布 / 回滚）这三类 skill。

## Decision

1. **重叠基准收敛为 mattpocock。** ECC fork 发布的 skill 与 mattpocock-skills 不得语义重叠：
   同一件事只留一个入口。已在 `full` profile 剔除 `blueprint`
   （与 mattpocock `wayfinder` 同属「把大块工作拆成多阶段计划」）；此前已剔除的
   `tdd-workflow`、`architecture-decision-records`、`context-and-decisions`、
   `intent-driven-development` 保持不变（见 ADR-0008 的接管方对照表）。
   `manifest/external_refs.json` 继续声明 `code-review` 由 mattpocock 提供。
2. **本机其它来源与 ECC 重叠时，ECC 优先。** addyosmani 库那 25 条未启用 skill 保持死链，
   不去启用；magpie 用户级那 4 条强重叠 skill 由 ECC 侧能力接管，用户级条目去留由用户决定，
   本 fork 不代为改动用户级配置。
3. **补齐发布 / 部署 / 运维。** 两手并行：
   - **放开上游已有的**：`production-audit`（上线前自检，按证据清单打 0–100 分，
     低于 70 不许上线）从 `java-python` 的排除列表移出，恢复发布；
     `dashboard-builder` 从 G10 移到 G2，使其进入 `java-python` profile；
     `lite` profile 仍排除这两个（保持最小集）。
   - **新写 fork 自有的三条**（`own/skills/`，始终物化，三个 profile 都带）：
     `ecc-omp-release-management`（打 tag、写 changelog、分级发布与回滚、制品可追溯）、
     `ecc-omp-observability`（日志 / 指标 / 追踪三支柱、SLO 与错误预算、告警设计）、
     `ecc-omp-incident-response`（P0–P3 定级、先止血后定位、沟通与复盘）。
     上游没有对应资产，这三条不构成与 mattpocock 的重叠。
4. **选路表同步接线。** `own/skills/ecc-omp-router/SKILL.md` 的「部署与运维」段补上
   release / observability / incident / dashboard / production-audit 五个入口。

## Alternatives Considered

### Alternative 1: 把上游 G10 整个选进 `java-python` profile

- **Pros**: 不用改分组，`dashboard-builder` 自然入选。
- **Cons**: G10 里 12 个成员大半是 UI 动效、产品文档、协作类（「非核心编程」组），
  与用户要的 ship / 运维方向无关，纯粹增加提示开销。
- **Why not**: 需要的是运维能力，不是整个 UI 组。

### Alternative 2: 新建 G11「发布 / 部署 / 运维」分组

- **Pros**: 运维能力在目录里成组可见，与 G2「通用工程规范」区分开。
- **Cons**: `manifest/groups.json` 的成员必须与 `pool/` 完全一致（`check_upstream_pin.py`
  校验摘要），新增分组要把成员从原组搬走，会改动上游分组语义；运维面目前只有
  `dashboard-builder` 一个成员需要搬，收益不抵改动量。
- **Why not**: 一个成员的移动用「调组」就够，不必重划分组体系。

### Alternative 3: 直接启用 addyosmani 库里的 `shipping-and-launch` 等 skill 替代自写

- **Pros**: 不用自己写。
- **Cons**: 用户明确说暂无启用该库的想法；且这三条是 ECC 侧能力，留在自己的插件里
  才能随 `omp plugin disable ecc-omp-fork` 一起启停，不受外部库状态影响。
- **Why not**: 与用户意图相反。

### Alternative 4: 只放开上游运维 skill，不自写

- **Pros**: 改动最小，零新增内容。
- **Cons**: 上游没有可观测性、事故响应、发布管理三类 skill，
  用户要的「ship / 部署 / 运维」只补上一半。
- **Why not**: 缺口是能力缺口，不是入口缺口。

## Consequences

### Positive

- `java-python` profile 下与 ship / 运维相关的入口从 3 个增加到 8 个：
  `deployment-patterns`、`docker-patterns`、`kubernetes-patterns`、`production-audit`、
  `dashboard-builder` + 自有的 `release-management`、`observability`、`incident-response`。
- 与 mattpocock 的重叠面清零到只剩「同一领域不同切入点」的边界情况，逐条判定写进本 ADR。
- 注入量小幅上升：`java-python` 从 ~4.6K token 到 ~4.9K（+2 个上游 skill + 3 条自有 skill
  的描述与运行名）。

### Negative

- `full` profile 的上游 skill 数从 128 降到 127（剔除 `blueprint`），
  `java-python` 从 63 升到 65。
- fork 自有 skill 从 1 条增到 4 条，`own/skills/` 的内容需要随上游同步一起维护。

### Risks

- 自写的三条运维 skill 没有上游来源可回溯，质量与时效要靠自己保证；
  与上游同类 skill 的关系靠 ADR-0008 的判重口径约束，未来上游若补上
  observability / incident-response 之类，需要重新判重。
- `production-audit` 的评分规则（低于 70 不许上线）是 ECC fork 的默认口径，
  项目自身门槛更高时以项目为准（`rule://fork-verification` 的既有分界）。
