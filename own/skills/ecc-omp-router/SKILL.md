---
name: ecc-omp-router
description: 本 fork（ECC 编程子集）的选路索引——把任务类型映射到实际存在的 skill / agent / command。开工前、或不确定该读哪个 skill、派哪个 agent、跑哪个命令时先读本表。注意：本表只覆盖高频资产，不是全集；未列出的技能看 skills/ 目录；表里的名字以当前 profile（java-python）为准，部分上游技能已被排除。
---

# 本 fork 的选路表

本 fork 只保留 ECC 的编程子集（上游全量 300+ 技能，本 fork 约 70 个）。
**本表是本 fork 的选路索引**：模型要读哪个 skill、派哪个 agent、跑哪个命令，以本表为准，
不要凭上游 ECC 的记忆猜名字——上游有大量技能没有进本 fork。

三类资源的分工：

| 资源 | 是什么 | 怎么用 |
| --- | --- | --- |
| **skill** | 知识与做法（怎么做对） | `read skill://<name>`，正文按需加载 |
| **agent** | 并行子任务（评审、探索、修复） | `task` 的 `agent` 字段，用**裸名** |
| **command** | 流程入口（规划、评审、提 PR） | 直接当斜杠命令用 |

下面的组合按「典型任务 → 读哪些 skill / 派哪些 agent / 跑哪些命令」给出。
**本表不覆盖全部资产**：没列出的技能仍然可用，查 `skills/` 目录即可。

---

## 新增一个后端接口

1. 读 skill：`api-design`（REST 约定）。Java 项目加 `springboot-patterns`，
   Python 项目加 `fastapi-patterns` / `django-patterns`。
   `backend-patterns` 是 Node.js/Express 专用，Java/Python 项目不要用它。
2. 数据层：读 `database-migrations`（迁移与回滚）、`postgres-patterns` / `mysql-patterns` /
   `prisma-patterns`（按项目实际存储选）、Java 项目加 `jpa-patterns` / `mybatis-patterns`。
3. 命令：`/plan` 先出实施计划（跨文件改动先确认再动手）。
4. 实现后：命令 `/test-coverage`；agent `code-reviewer`（通用）或 `java-reviewer` / `python-reviewer`（语言专项）。
5. 涉及鉴权或用户数据时：读 skill `security-review`，再派 `security-reviewer`。

## 修一个 bug

1. 先复现再改。读 skill `error-handling`（错误路径与兜底；Python/Go/TS 场景适用，
   Java 场景配 `springboot-patterns`）。
2. 加能复现该 bug 的回归测试（见规则 `fork-verification`）。
3. 改完跑目标测试，贴真实输出；收工前跑一遍 `verification-loop` 的六阶段验证。
4. 派 `silent-failure-hunter` 排查同类的吞错/坏兜底。
5. 命令 `/refactor-clean` 只在顺手清理死代码时用，别顺手扩大范围。

## 写或改测试

1. 读 skill：`tdd-workflow`（方法）、`test-collaboration`（协作）、对应语言的测试 skill
   （`python-testing` / `django-tdd` / `springboot-tdd` / `kotlin-testing` / `golang-testing` /
   `rust-testing` / `cpp-testing` / `perl-testing` / `fsharp-testing` / `react-testing` …）。
2. agent：`tdd-guide` 负责写测试优先的流程。
3. 端到端：agent `e2e-runner`；skill `e2e-testing`。
4. 覆盖率缺口：命令 `/test-coverage`。
5. 框架自带的完整门禁：Java 读 `springboot-verification`，Python 读 `django-verification`。

## 评审代码

1. 命令 `/code-review`（本地未提交改动）或 `/pr` 流程中的评审环节。
   本 fork 里 `code-review` 只有**命令**这一形态；别的插件若提供同名 skill，
   要读它必须写 `skill://code-review`。命令写 `/code-review`，skill 写 `skill://code-review`，
   两种写法别混。
2. agent：`code-reviewer`（通用）、`java-reviewer` / `kotlin-reviewer` / `python-reviewer` /
   `django-reviewer` / `fastapi-reviewer`（语言与框架专项）、`security-reviewer`（安全）、
   `silent-failure-hunter`（吞错）、`comment-analyzer`（注释质量）。
3. 通用规范对照：skill `coding-standards`。
4. PR 的测试覆盖质量：agent `pr-test-analyzer`。
5. FastAPI 项目还有专门命令 `/fastapi-review`。
6. 提交信息：agent `commit-reviewer`，或命令 `/prp-commit`；skill `conventional-commit-review`。

## 重构 / 清理

1. 读 skill `inherit-legacy-style`（先理解旧代码再动）、`codebase-onboarding`（陌生仓库先摸清）。
2. 影响面先量化：读 skill `change-impact`（跨文件改动先确认影响范围）。
3. agent `refactor-cleaner`（死代码）、`code-simplifier`（可读性）、`code-explorer`（并行摸清陌生代码）。
4. 改完必须跑测试证明没破坏行为。

## 架构与设计

1. agent `architect`（系统设计）、`code-architect`（特性架构）、`planner`（实施计划）。
2. 读 skill `architecture-decision-records`（决策记录）、`hexagonal-architecture`、`contract-first`。
3. 命令 `/plan-prd`（问题优先的精简 PRD）、`/prp-prd`（交互式 PRD）、`/prp-plan`（带代码库分析的详细计划）、
   `/prp-implement`（执行已有计划）。
4. 需求本身含糊时：读 skill `intent-driven-development`（把模糊需求转成可验证的验收标准）。

## 性能问题

1. agent `performance-optimizer`（定位瓶颈、给优化方案）。
2. 动手前读 skill `change-impact`（先量化影响面），改完读 skill `verification-loop`（跑完验证闭环再收工）。
3. 数据吞吐类问题按项目实际存储读 `postgres-patterns` / `mysql-patterns` / `redis-patterns`。

## 部署与运维

1. 读 skill `docker-patterns`、`kubernetes-patterns`、`deployment-patterns`。
2. agent `network-troubleshooter`（连通性/DNS/路由）、`network-config-reviewer`（设备配置审查）。
3. 构建失败：命令 `/build-fix`（通用）；agent `build-error-resolver`（通用）、
   `java-build-resolver`（JVM）、`django-build-resolver`（Python）。
   `/gradle-build` 是 Android/KMP 专用，JVM 后端构建失败不要用它。

## 文档

1. 命令 `/update-docs`（从脚本/路由/导出等真相源同步文档）、`/update-codemaps`（生成架构地图）。
2. agent `code-explorer`（先摸清代码与文档的对应关系，再决定改哪份）。
3. 读 skill `docs-governance`（文档治理口径）。

## 提交与 PR

1. 命令 `/prp-commit`（自然语言描述要提交什么）、`/pr`（建 PR）、`/prp-pr`（PRP 流程中建 PR）。
2. agent `commit-reviewer`（生成符合 Conventional Commits 的提交信息）。
3. 分支策略 / 合并方式 / rebase 与 merge 的取舍：读 skill `git-workflow`。

## 跨语言 / 冷门栈

本 fork 的 Java/Kotlin、Python/Django/FastAPI 最全。其他语言按需：
`golang-patterns` `rust-patterns` `cpp-coding-standards` `perl-patterns` `csharp-testing` 等，
`/go-test` `/rust-test` `/cpp-test` `/kotlin-test` `/react-test` `/flutter-test` 是对应语言的 TDD 命令。

---

## 拿不准的时候

- 先读本表对应的 skill 正文，再决定要不要派 agent。
- 规则（`rule://`）里是硬约束（工具名、验证纪律、密钥处理），skill 里是做法建议。
  两者冲突时以规则为准。
- 如果某个 skill 读不到，说明当前 profile 没启用它；查 `manifest/selection.json` 或换 profile。
- 本表没提到的技能不代表不存在，查 `skills/` 目录；表里的名字则保证在当前 profile 下真实存在。
