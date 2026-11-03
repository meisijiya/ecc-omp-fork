---
name: forge-router
description: 当用户要开工、要决定读哪条 skill 或派哪个 agent 时，先读这张表挑本 fork 的资产（名字都带 forge- 前缀）：接口设计、数据库、测试、评审、发布、运维、文档、跨语言栈。已经知道要读哪条时不要读它。
---

# 本 fork 的选路表

本 fork 只保留 ECC 的编程子集加两支收纳资产（上游全量 300+ 技能，本 fork 默认 profile 约 86 个：65 条上游 + 17 条收纳 + 4 条自有）。
**本表是本 fork 的选路索引**：模型要读哪个 skill、派哪个 agent，以本表为准，
不要凭上游 ECC 的记忆猜名字——上游有大量技能没有进本 fork。

**读完这张表后的动作**：立刻 `read skill://<表里对应的名字>` 读正文，再动手写代码。
只读完表就开始实现，等于没用这张表。

两类资源的分工：

| 资源 | 是什么 | 怎么用 |
| --- | --- | --- |
| **skill** | 知识与做法（怎么做对） | `read skill://<name>`，正文按需加载 |
| **agent** | 并行子任务（评审、探索、修复） | `task` 的 `agent` 字段，用**带前缀的裸名** |

本 fork 物化出来的 skill / agent 全部带 `forge-` 前缀（上游名不带），
这样和其他插件的同名资产不会撞车；下面表里写的就是运行时的名字。

下面的组合按「典型任务 → 读哪些 skill / 派哪些 agent」给出。
**本表不覆盖全部资产**：没列出的技能仍然可用，查 `skills/` 目录即可。

---

## 按用户的话找 skill（先查这张表）

接口与数据：

| 用户可能这么说 | 读 / 派 |
| --- | --- |
| 写接口、加接口、接口怎么定 | `forge-api-design` |
| 跨服务契约先定下来 | `forge-contract-first` |
| 建表、改表、加字段、迁移 | `forge-database-migrations` 加对应数据库 skill |
| 查询慢、索引怎么建 | `forge-postgres-patterns` 或 `forge-mysql-patterns` |
| 缓存怎么放、什么能缓存 | `forge-content-hash-cache-pattern` |
| 校验登录、鉴权、权限、越权 | `forge-security-review` |

测试与评审：

| 用户可能这么说 | 读 / 派 |
| --- | --- |
| 补测试、写单测 | 对应语言的 `forge-python-testing` 一类，框架用 `forge-django-tdd` 一类 |
| 端到端、浏览器里点一遍 | `forge-e2e-testing`，agent `forge-e2e-runner` |
| 测试覆盖够不够、缺哪些 | `forge-test-collaboration` |
| 这次改动会影响到哪里 | `forge-change-impact` |
| 帮我评审这次改动 | agent `forge-java-reviewer` 或 `forge-python-reviewer` |
| 报错、异常被吞、兜底不对 | `forge-error-handling`，agent `forge-silent-failure-hunter` |
| 同一个错反复犯 | `forge-correct` |

测试全流程（QA 套件，收纳自 fishzjp/qa-skills；`forge-qa` 是编排入口，其余按阶段读）：

| 用户可能这么说 | 读 / 派 |
| --- | --- |
| 把这个需求从理解到报告测一遍 | `forge-qa`（阶段编排、断点续跑） |
| 需求还没摸清，先把范围与规则问清 | `forge-requirement-analysis` |
| 这次该测什么、测到什么深度 | `forge-test-strategy` |
| 把需求写成可执行用例 | `forge-test-case-writing` |
| 用例写完了，审一遍够不够严 | `forge-test-case-review` |
| 需求含糊、系统陌生，先探索一轮 | `forge-exploratory-testing` |
| 接口怎么测、要压测脚本 | `forge-api-testing` |
| 这是 Bug 吗、根因和影响面在哪 | `forge-bug-analysis` |
| 改完代码该回归哪些 | `forge-regression-testing` |
| 测试反复红、是不是 flaky | `forge-test-reliability` |
| 项目踩过的坑要跨会话记住 | `forge-qa-memory` |
| 用例格式、证据分级、风险模型、报告模板、校验脚本 | `forge-core`（共享知识库，其余 QA skill 都引用它，不要单独当工作流用） |

写 Playwright 测试本身读 `forge-e2e-testing`（ECC 的工程模式）；要的是「跑完一整条端到端
测试流程并出报告」则走 `forge-qa` 编排，执行阶段由 `forge-automated-e2e-testing` 接。

交付与运维：

| 用户可能这么说 | 读 / 派 |
| --- | --- |
| 发版、打 tag、写 changelog | `forge-release-management` |
| 上线前检查一遍 | `forge-production-audit` 与 `forge-constraint-driven-development` |
| 容器、镜像、compose | `forge-docker-patterns` |
| K8s、探针、RBAC | `forge-kubernetes-patterns` |
| 看日志、指标、告警 | `forge-observability` |
| 同步上游、发布或部署这个插件本身 | `forge-pipeline` |
| 这个插件的 CI 挂了 | `forge-ci-triage` |
| 要把第三方仓库的 skill 收进本插件 | `forge-absorb-third-party-skill` |
| 线上挂了、出事故 | `forge-incident-response` |
| 监控面板怎么排 | `forge-dashboard-builder` |
| 性能慢、要不要优化 | agent `forge-performance-optimizer` |

代码与语言：

| 用户可能这么说 | 读 / 派 |
| --- | --- |
| 代码太乱、清死代码 | agent `forge-refactor-cleaner` 或 `forge-code-simplifier` |
| 不熟这个仓库、先摸清 | `forge-codebase-onboarding` 与 `forge-code-tour` |
| 分支、合并、rebase | `forge-git-workflow` |
| 提交信息怎么写 | `forge-conventional-commit-review` |
| 文档怎么写、文档过时了 | `forge-docs-governance` |
| 构建挂了、编译报错 | agent `forge-build-error-resolver` |
| 状态机、流程会不会走错 | `forge-statechart`（仅 full） |
| 任务太浅、先想深一点 | `forge-sharpen` |
| 幂等、重试、并发共享状态 | `forge-engineering-principles` |

按语言挑一条：

| 用户可能这么说 | 读 |
| --- | --- |
| Java、Spring、JPA 怎么写 | `forge-springboot-patterns` 与 `forge-jpa-patterns` |
| Python、Django、FastAPI 怎么写 | `forge-django-patterns` 与 `forge-fastapi-patterns` |
| 其它语言栈 | `forge-golang-patterns` 一类，按语言选一条 |

---

## 新增一个后端接口

1. 读 skill：`skill://forge-api-design`（REST 约定）。Java 项目加 `skill://forge-springboot-patterns`，
 Python 项目加 `skill://forge-fastapi-patterns` / `skill://forge-django-patterns`。
 `skill://forge-backend-patterns` 是 Node.js/Express 专用，Java/Python 项目不要用它。
2. 数据层：读 `skill://forge-database-migrations`（迁移与回滚）、`skill://forge-postgres-patterns` / `skill://forge-mysql-patterns` /
 `skill://forge-prisma-patterns`（按项目实际存储选），Java 项目加 `skill://forge-jpa-patterns` / `skill://forge-mybatis-patterns`。
3. 跨服务契约先行：读 `skill://forge-contract-first`。
4. 实现后：agent `forge-java-reviewer` / `forge-python-reviewer`（语言专项）做专项评审。
5. 涉及鉴权或用户数据时：读 `skill://forge-security-review`。

## 修一个 bug

1. 先复现再改。读 `skill://forge-error-handling`（错误路径与兜底；Python/Go/TS 场景适用，
 Java 场景配 `skill://forge-springboot-patterns`）。
2. 加能复现该 bug 的回归测试（见规则 `rule://fork-verification`）。
3. 改完跑目标测试，贴真实输出；收工前跑一遍 `skill://forge-verification-loop` 的六阶段验证。
4. 派 `forge-silent-failure-hunter` 排查同类的吞错/坏兜底。
5. 同一个错误被纠正过两次：读 `skill://forge-correct`，把它变成架构、类型、lint 或测试上的约束，
 而不是再写一遍提醒。

## 写或改测试

1. 读 skill：对应语言的测试 skill（`skill://forge-python-testing` / `skill://forge-django-tdd` /
 `skill://forge-springboot-tdd` / `skill://forge-kotlin-testing` / `skill://forge-golang-testing` /
 `skill://forge-rust-testing` / `skill://forge-cpp-testing` /
 `skill://forge-perl-testing` / `skill://forge-fsharp-testing` / `skill://forge-csharp-testing` /
 `skill://forge-react-testing`）。
2. 测试资产治理、覆盖缺口分析：读 `skill://forge-test-collaboration`。
3. 要把整条链路走一遍（需求 → 策略 → 用例 → 执行 → 报告）：读 `skill://forge-qa` 编排，
   按阶段读 `skill://forge-requirement-analysis`、`skill://forge-test-strategy`、
   `skill://forge-test-case-writing`；格式、证据分级、报告模板与 `scripts/` 校验器都在
   `skill://forge-core`。用例落盘后用 `forge-core` 自带校验器复验（调用写法见
   `rule://omp-tooling` 的技能脚本路径一节）。
4. 端到端：agent `forge-e2e-runner`；`skill://forge-e2e-testing`；把可自动化的用例变成
   代码并回填证据读 `skill://forge-automated-e2e-testing`。
5. 框架自带的完整门禁：Java 读 `skill://forge-springboot-verification`，Python 读 `skill://forge-django-verification`。

## 评审代码

1. agent：`forge-java-reviewer` / `forge-kotlin-reviewer` / `forge-python-reviewer` /
 `forge-django-reviewer` / `forge-fastapi-reviewer`（语言与框架专项）、`forge-comment-analyzer`（注释质量）、
 `forge-silent-failure-hunter`（吞错）、`forge-type-design-analyzer`（类型设计）。
2. 通用规范对照：`skill://forge-coding-standards`。
3. 提交信息：`skill://forge-conventional-commit-review`。
4. 通用层评审（跨语言）：agent `forge-architect`、`forge-database-reviewer`。

## 重构 / 清理

1. 读 `skill://forge-inherit-legacy-style`（先理解旧代码再动）、`skill://forge-codebase-onboarding`（陌生仓库先摸清）。
2. 影响面先量化：读 `skill://forge-change-impact`（跨文件改动先确认影响范围）。
3. agent `forge-refactor-cleaner`（死代码）、`forge-code-simplifier`（可读性）。
4. 改完必须跑测试证明没破坏行为。

## 架构与设计

1. agent `forge-architect`（系统设计、扩展性）、`forge-homelab-architect`（家用网络与实验环境）。
2. 读 `skill://forge-hexagonal-architecture`（端口与适配器）、`skill://forge-contract-first`。
3. 状态机、协议、多阶段流程要证明规则不被违反：读 `skill://forge-statechart`（TLA+ 模型检查 +
 Mermaid 状态图，报告给最短违例路径；仅 full profile）。
4. 需求本身含糊时：先把需求拆成可验证的验收标准，再动手。

## 性能问题

1. agent `forge-performance-optimizer`（定位瓶颈、给优化方案）。
2. 动手前读 `skill://forge-change-impact`（先量化影响面），改完读 `skill://forge-verification-loop`（跑完验证闭环再收工）。
3. 数据吞吐类问题按项目实际存储读 `skill://forge-postgres-patterns` / `skill://forge-mysql-patterns` / `skill://forge-redis-patterns`。

## 构建失败

1. agent `forge-build-error-resolver`（通用）、`forge-java-build-resolver`（JVM）、`forge-kotlin-build-resolver`（KMP）、
 `forge-django-build-resolver`（Python/Django）。

## 部署与运维

1. 读 `skill://forge-docker-patterns`、`skill://forge-kubernetes-patterns`、`skill://forge-deployment-patterns`（容器、编排、发布策略）。
2. 发版：读 `skill://forge-release-management`（打 tag、写 changelog、分级发布与回滚、制品可追溯）。
3. 上线后要「看得见」：读 `skill://forge-observability`（日志 / 指标 / 追踪、SLO 与错误预算、告警设计）；
   监控面板本身读 `skill://forge-dashboard-builder`。
4. 出线上事故：读 `skill://forge-incident-response`（定级、止血与回滚决策、沟通记录、复盘）。
5. 上线前自检：读 `skill://forge-production-audit`（按证据清单给 0–100 分，低于 70 不许上线）。
6. 项目还没有写下来的质量底线（覆盖率、包体积、可访问性、安全扫描）：读
   `skill://forge-constraint-driven-development`，把底线写成 CONSTRAINTS.md 并盯住 diff 里被悄悄降的门槛。
7. agent `forge-network-troubleshooter`（连通性/DNS/路由）、`forge-network-config-reviewer`（设备配置审查）。

## 文档

1. 读 `skill://forge-docs-governance`（文档治理口径）。
2. 陌生代码库的结构导览：`skill://forge-codebase-onboarding`；带示例的源码导览：`skill://forge-code-tour`。

## 分支与提交

1. 分支策略 / 合并方式 / rebase 与 merge 的取舍：读 `skill://forge-git-workflow`。
2. 提交信息：`skill://forge-conventional-commit-review`。

## 跨语言 / 冷门栈

本 fork 的 Java/Kotlin、Python/Django/FastAPI 最全。其他语言按需：
`skill://forge-golang-patterns` `skill://forge-rust-patterns` `skill://forge-cpp-coding-standards` `skill://forge-perl-patterns` `skill://forge-csharp-testing`
`skill://forge-bun-runtime` `skill://forge-compose-multiplatform-patterns` `skill://forge-nestjs-patterns` `skill://forge-nextjs-turbopack`
`skill://forge-vite-patterns` `skill://forge-vue-patterns` `skill://forge-react-patterns`。

## 补缺（收纳资产）

这几条来自 fork 之外、经改写后随本 fork 发布（来源与 pin 记在 `manifest/absorbed.json`），
上游 ECC 与 mattpocock 都没有对应条目：

| 要解决的事 | 读什么 |
| --- | --- |
| 同一个错误被反复纠正，要让它不可能再犯 | `skill://forge-correct` |
| 项目没有写下来的质量底线，或有人靠改阈值/跳过测试变绿 | `skill://forge-constraint-driven-development` |
| 任务本身不够深（不是不够大），要重写任务再动手 | `skill://forge-sharpen` |
| 非平凡工作的通用工程原则（幂等、可验证单元、共享状态、设计空间、第一性原理、体验优先） | `skill://forge-engineering-principles` |
| 状态机 / 协议 / 多阶段流程要证明规则不被违反 | `skill://forge-statechart`（仅 full profile） |
| 读写 `.ts` / `.tsx` | `skill://forge-typescript-patterns`（仅 full profile；严格编译配置、类型设计与窄化） |
| 测试从需求到报告整条链路怎么走 | `skill://forge-qa`（收纳自 fishzjp/qa-skills，`forge-core` 是它的共享知识库；`lite` 不收） |

---

## 拿不准的时候

- 先读本表对应的 skill 正文，再决定要不要派 agent。
- 拿不准该读哪条时，先看 `skill://forge-engineering-principles` 有没有对应小节，比通读本表快。
- 规则（`rule://`）里是硬约束（工具名、验证纪律、密钥处理），skill 里是做法建议。
  两者冲突时以规则为准。
- 如果某个 skill 读不到，说明当前 profile 没启用它；查 `manifest/selection.json` 或换 profile。
- 本表没提到的技能不代表不存在，查 `skills/` 目录；表里的名字属于本 fork 的完整目录，在当前 profile 下可能被裁掉（`lite` 只留一部分语言栈）。
