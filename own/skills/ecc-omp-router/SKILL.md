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
| **agent** | 并行子任务（评审、探索、修复） | `task` 的 `agent` 字段，用**带前缀的裸名** |
| **command** | 流程入口（规划、评审、提 PR） | 直接当斜杠命令用 |

本 fork 物化出来的 skill / command / agent 全部带 `ecc-omp-` 前缀（上游原名不带），
这样和其他插件的同名资产不会撞车；下面表里写的就是运行时的名字。

下面的组合按「典型任务 → 读哪些 skill / 派哪些 agent / 跑哪些命令」给出。
**本表不覆盖全部资产**：没列出的技能仍然可用，查 `skills/` 目录即可。

---

## 新增一个后端接口

1. 读 skill：`skill://ecc-omp-api-design`（REST 约定）。Java 项目加 `skill://ecc-omp-springboot-patterns`，
 Python 项目加 `skill://ecc-omp-fastapi-patterns` / `skill://ecc-omp-django-patterns`。
 `skill://ecc-omp-backend-patterns` 是 Node.js/Express 专用，Java/Python 项目不要用它。
2. 数据层：读 `skill://ecc-omp-database-migrations`（迁移与回滚）、`skill://ecc-omp-postgres-patterns` / `skill://ecc-omp-mysql-patterns` /
 `skill://ecc-omp-prisma-patterns`（按项目实际存储选）、Java 项目加 `skill://ecc-omp-jpa-patterns` / `skill://ecc-omp-mybatis-patterns`。
3. 命令：`/ecc-omp-plan` 先出实施计划（跨文件改动先确认再动手）。
4. 实现后：命令 `/ecc-omp-test-coverage`；agent `ecc-omp-code-reviewer`（通用）或 `ecc-omp-java-reviewer` / `ecc-omp-python-reviewer`（语言专项）。
5. 涉及鉴权或用户数据时：读 `skill://ecc-omp-security-review`，再派 `ecc-omp-security-reviewer`。

## 修一个 bug

1. 先复现再改。读 `skill://ecc-omp-error-handling`（错误路径与兜底；Python/Go/TS 场景适用，
 Java 场景配 `skill://ecc-omp-springboot-patterns`）。
2. 加能复现该 bug 的回归测试（见规则 `rule://fork-verification`）。
3. 改完跑目标测试，贴真实输出；收工前跑一遍 `skill://ecc-omp-verification-loop` 的六阶段验证。
4. 派 `ecc-omp-silent-failure-hunter` 排查同类的吞错/坏兜底。
5. 命令 `/ecc-omp-refactor-clean` 只在顺手清理死代码时用，别顺手扩大范围。

## 写或改测试

1. 读 skill：`skill://ecc-omp-tdd-workflow`（方法）、`skill://ecc-omp-test-collaboration`（协作）、对应语言的测试 skill
 （`skill://ecc-omp-python-testing` / `skill://ecc-omp-django-tdd` / `skill://ecc-omp-springboot-tdd` / `skill://ecc-omp-kotlin-testing` / `skill://ecc-omp-golang-testing` /
 `skill://ecc-omp-rust-testing` / `skill://ecc-omp-cpp-testing` / `skill://ecc-omp-perl-testing` / `skill://ecc-omp-fsharp-testing` / `skill://ecc-omp-react-testing` …）。
2. agent：`ecc-omp-tdd-guide` 负责写测试优先的流程。
3. 端到端：agent `ecc-omp-e2e-runner`；`skill://ecc-omp-e2e-testing`。
4. 覆盖率缺口：命令 `/ecc-omp-test-coverage`。
5. 框架自带的完整门禁：Java 读 `skill://ecc-omp-springboot-verification`，Python 读 `skill://ecc-omp-django-verification`。

## 评审代码

1. 命令 `/ecc-omp-code-review`（本地未提交改动）或 `/ecc-omp-pr` 流程中的评审环节。
   本 fork 的评审**命令**带前缀，叫 `/ecc-omp-code-review`；别的插件提供的同名 skill 不带前缀
   （要读它写 `skill://code-review`）。两种写法别混。
2. agent：`ecc-omp-code-reviewer`（通用）、`ecc-omp-java-reviewer` / `ecc-omp-kotlin-reviewer` / `ecc-omp-python-reviewer` /
 `ecc-omp-django-reviewer` / `ecc-omp-fastapi-reviewer`（语言与框架专项）、`ecc-omp-security-reviewer`（安全）、
 `ecc-omp-silent-failure-hunter`（吞错）、`ecc-omp-comment-analyzer`（注释质量）。
3. 通用规范对照：`skill://ecc-omp-coding-standards`。
4. PR 的测试覆盖质量：agent `ecc-omp-pr-test-analyzer`。
5. FastAPI 项目还有专门命令 `/ecc-omp-fastapi-review`。
6. 提交信息：agent `ecc-omp-commit-reviewer`，或命令 `/ecc-omp-prp-commit`；`skill://ecc-omp-conventional-commit-review`。

## 重构 / 清理

1. 读 `skill://ecc-omp-inherit-legacy-style`（先理解旧代码再动）、`skill://ecc-omp-codebase-onboarding`（陌生仓库先摸清）。
2. 影响面先量化：读 `skill://ecc-omp-change-impact`（跨文件改动先确认影响范围）。
3. agent `ecc-omp-refactor-cleaner`（死代码）、`ecc-omp-code-simplifier`（可读性）、`ecc-omp-code-explorer`（并行摸清陌生代码）。
4. 改完必须跑测试证明没破坏行为。

## 架构与设计

1. agent `ecc-omp-architect`（系统设计）、`ecc-omp-code-architect`（特性架构）、`ecc-omp-planner`（实施计划）。
2. 读 `skill://ecc-omp-architecture-decision-records`（决策记录）、`skill://ecc-omp-hexagonal-architecture`、`skill://ecc-omp-contract-first`。
3. 命令 `/ecc-omp-plan-prd`（问题优先的精简 PRD）、`/ecc-omp-prp-prd`（交互式 PRD）、`/ecc-omp-prp-plan`（带代码库分析的详细计划）、
 `/ecc-omp-prp-implement`（执行已有计划）。
4. 需求本身含糊时：读 `skill://ecc-omp-intent-driven-development`（把模糊需求转成可验证的验收标准）。

## 性能问题

1. agent `ecc-omp-performance-optimizer`（定位瓶颈、给优化方案）。
2. 动手前读 `skill://ecc-omp-change-impact`（先量化影响面），改完读 `skill://ecc-omp-verification-loop`（跑完验证闭环再收工）。
3. 数据吞吐类问题按项目实际存储读 `skill://ecc-omp-postgres-patterns` / `skill://ecc-omp-mysql-patterns` / `skill://ecc-omp-redis-patterns`。

## 部署与运维

1. 读 `skill://ecc-omp-docker-patterns`、`skill://ecc-omp-kubernetes-patterns`、`skill://ecc-omp-deployment-patterns`。
2. agent `ecc-omp-network-troubleshooter`（连通性/DNS/路由）、`ecc-omp-network-config-reviewer`（设备配置审查）。
3. 构建失败：命令 `/ecc-omp-build-fix`（通用）；agent `ecc-omp-build-error-resolver`（通用）、
 `ecc-omp-java-build-resolver`（JVM）、`ecc-omp-django-build-resolver`（Python）。
 `/ecc-omp-gradle-build` 是 Android/KMP 专用，JVM 后端构建失败不要用它。

## 文档

1. 命令 `/ecc-omp-update-docs`（从脚本/路由/导出等真相源同步文档）、`/ecc-omp-update-codemaps`（生成架构地图）。
2. agent `ecc-omp-code-explorer`（先摸清代码与文档的对应关系，再决定改哪份）。
3. 读 `skill://ecc-omp-docs-governance`（文档治理口径）。

## 提交与 PR

1. 命令 `/ecc-omp-prp-commit`（自然语言描述要提交什么）、`/ecc-omp-pr`（建 PR）、`/ecc-omp-prp-pr`（PRP 流程中建 PR）。
2. agent `ecc-omp-commit-reviewer`（生成符合 Conventional Commits 的提交信息）。
3. 分支策略 / 合并方式 / rebase 与 merge 的取舍：读 `skill://ecc-omp-git-workflow`。

## 跨语言 / 冷门栈

本 fork 的 Java/Kotlin、Python/Django/FastAPI 最全。其他语言按需：
`skill://ecc-omp-golang-patterns` `skill://ecc-omp-rust-patterns` `skill://ecc-omp-cpp-coding-standards` `skill://ecc-omp-perl-patterns` `skill://ecc-omp-csharp-testing` 等，
`/ecc-omp-go-test` `/ecc-omp-rust-test` `/ecc-omp-cpp-test` `/ecc-omp-kotlin-test` `/ecc-omp-react-test` `/ecc-omp-flutter-test` 是对应语言的 TDD 命令。

---

## 拿不准的时候

- 先读本表对应的 skill 正文，再决定要不要派 agent。
- 规则（`rule://`）里是硬约束（工具名、验证纪律、密钥处理），skill 里是做法建议。
  两者冲突时以规则为准。
- 如果某个 skill 读不到，说明当前 profile 没启用它；查 `manifest/selection.json` 或换 profile。
- 本表没提到的技能不代表不存在，查 `skills/` 目录；表里的名字属于本 fork 的完整目录，在当前 profile 下可能被裁掉（`lite` 只留一部分语言栈）。
