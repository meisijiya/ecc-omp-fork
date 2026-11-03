# ECC-OMP-Fork 资产目录

> 由 `tools/build_catalog.py` 生成，勿手改。
> 上游：[affaan-m/ECC](https://github.com/affaan-m/ECC)（MIT）。

当前生效 profile：**java-python**。

| profile | 说明 | skills | commands | agents |
| --- | --- | --- | --- | --- |
| `full` | 上游 pi/core 全量技能（去掉与其它插件重复的 5 个）加编程相关 agent。不含命令。token 开销最大，仅在需要冷门技术栈时用。 | 147 | 0 | 49 |
| `java-python` | Java/Kotlin + Python/Django/FastAPI 主力 + 通用工程规范。面向后端/测试开发日常。 | 82 | 0 | 22 |
| `lite` | 最小可用集：只保留后端核心规范 + Java/Python 主力 + 通用评审 agent。每轮提示开销最低。 | 39 | 0 | 11 |

> 表里的**运行名**是本 fork 物化后实际使用的名字：上游名统一加 `forge-` 前缀（skill / command / agent）。
> 「上游名」是 affaan-m/ECC 里的名称，用于回溯上游来源；组列写「收纳」的资产来自 fork 之外的仓库，经改写后随本 fork 发布（ADR-0010，来源见 `manifest/absorbed.json`），它们的「上游名」一列是来源仓库里的名字，不是 ECC 名。

## Skills

| 组 | 名称（运行名） | 上游名 | 生效 profile |
| --- | --- | --- | --- |
| G1 | ✅ `forge-api-design` | `api-design` | full, java-python, lite |
| G1 | ✅ `forge-backend-patterns` | `backend-patterns` | full, java-python, lite |
| G1 | ✅ `forge-hexagonal-architecture` | `hexagonal-architecture` | full, java-python, lite |
| G1 | ⬜ `forge-architecture-decision-records` | `architecture-decision-records` | — |
| G1 | ✅ `forge-contract-first` | `contract-first` | full, java-python, lite |
| G1 | ⬜ `forge-api-connector-builder` | `api-connector-builder` | full |
| G1 | ✅ `forge-content-hash-cache-pattern` | `content-hash-cache-pattern` | full, java-python |
| G1 | ✅ `forge-regex-vs-llm-structured-text` | `regex-vs-llm-structured-text` | full, java-python, lite |
| G1 | ⬜ `forge-mcp-server-patterns` | `mcp-server-patterns` | full |
| G2 | ✅ `forge-coding-standards` | `coding-standards` | full, java-python, lite |
| G2 | ✅ `forge-error-handling` | `error-handling` | full, java-python, lite |
| G2 | ⬜ `forge-intent-driven-development` | `intent-driven-development` | — |
| G2 | ✅ `forge-change-impact` | `change-impact` | full, java-python, lite |
| G2 | ⬜ `forge-context-and-decisions` | `context-and-decisions` | — |
| G2 | ✅ `forge-inherit-legacy-style` | `inherit-legacy-style` | full, java-python, lite |
| G2 | ✅ `forge-code-tour` | `code-tour` | full, java-python, lite |
| G2 | ✅ `forge-codebase-onboarding` | `codebase-onboarding` | full, java-python, lite |
| G2 | ✅ `forge-conventional-commit-review` | `conventional-commit-review` | full, java-python, lite |
| G2 | ✅ `forge-git-workflow` | `git-workflow` | full, java-python, lite |
| G2 | ✅ `forge-docs-governance` | `docs-governance` | full, java-python, lite |
| G2 | ⬜ `forge-living-docs-governance` | `living-docs-governance` | full |
| G2 | ✅ `forge-security-review` | `security-review` | full, java-python, lite |
| G2 | ⬜ `forge-tdd-workflow` | `tdd-workflow` | — |
| G2 | ✅ `forge-test-collaboration` | `test-collaboration` | full, java-python, lite |
| G2 | ✅ `forge-verification-loop` | `verification-loop` | full, java-python, lite |
| G2 | ⬜ `forge-module-regression` | `module-regression` | full |
| G2 | ✅ `forge-e2e-testing` | `e2e-testing` | full, java-python, lite |
| G2 | ✅ `forge-production-audit` | `production-audit` | full, java-python |
| G2 | ⬜ `forge-parallel-execution-optimizer` | `parallel-execution-optimizer` | full |
| G2 | ⬜ `forge-benchmark` | `benchmark` | full |
| G2 | ⬜ `forge-benchmark-optimization-loop` | `benchmark-optimization-loop` | full |
| G2 | ⬜ `forge-latency-critical-systems` | `latency-critical-systems` | full |
| G2 | ✅ `forge-deployment-patterns` | `deployment-patterns` | full, java-python, lite |
| G2 | ✅ `forge-docker-patterns` | `docker-patterns` | full, java-python, lite |
| G2 | ✅ `forge-kubernetes-patterns` | `kubernetes-patterns` | full, java-python, lite |
| G2 | ✅ `forge-dashboard-builder` | `dashboard-builder` | full, java-python |
| G3 | ✅ `forge-java-coding-standards` | `java-coding-standards` | full, java-python, lite |
| G3 | ✅ `forge-springboot-patterns` | `springboot-patterns` | full, java-python, lite |
| G3 | ✅ `forge-springboot-security` | `springboot-security` | full, java-python, lite |
| G3 | ✅ `forge-springboot-tdd` | `springboot-tdd` | full, java-python, lite |
| G3 | ✅ `forge-springboot-verification` | `springboot-verification` | full, java-python, lite |
| G3 | ✅ `forge-jpa-patterns` | `jpa-patterns` | full, java-python |
| G3 | ✅ `forge-mybatis-patterns` | `mybatis-patterns` | full, java-python |
| G3 | ✅ `forge-kotlin-patterns` | `kotlin-patterns` | full, java-python, lite |
| G3 | ✅ `forge-kotlin-testing` | `kotlin-testing` | full, java-python, lite |
| G3 | ⬜ `forge-kotlin-coroutines-flows` | `kotlin-coroutines-flows` | full |
| G3 | ⬜ `forge-kotlin-exposed-patterns` | `kotlin-exposed-patterns` | full |
| G3 | ⬜ `forge-kotlin-ktor-patterns` | `kotlin-ktor-patterns` | full |
| G4 | ✅ `forge-python-patterns` | `python-patterns` | full, java-python, lite |
| G4 | ✅ `forge-python-testing` | `python-testing` | full, java-python, lite |
| G4 | ✅ `forge-django-patterns` | `django-patterns` | full, java-python, lite |
| G4 | ✅ `forge-django-tdd` | `django-tdd` | full, java-python, lite |
| G4 | ✅ `forge-django-verification` | `django-verification` | full, java-python, lite |
| G4 | ✅ `forge-django-security` | `django-security` | full, java-python, lite |
| G4 | ✅ `forge-django-celery` | `django-celery` | full, java-python |
| G4 | ✅ `forge-fastapi-patterns` | `fastapi-patterns` | full, java-python, lite |
| G5 | ✅ `forge-golang-patterns` | `golang-patterns` | full, java-python |
| G5 | ✅ `forge-golang-testing` | `golang-testing` | full, java-python |
| G5 | ✅ `forge-rust-patterns` | `rust-patterns` | full, java-python |
| G5 | ✅ `forge-rust-testing` | `rust-testing` | full, java-python |
| G5 | ✅ `forge-cpp-coding-standards` | `cpp-coding-standards` | full, java-python |
| G5 | ✅ `forge-cpp-testing` | `cpp-testing` | full, java-python |
| G5 | ✅ `forge-csharp-testing` | `csharp-testing` | full, java-python |
| G5 | ✅ `forge-fsharp-testing` | `fsharp-testing` | full, java-python |
| G5 | ✅ `forge-perl-patterns` | `perl-patterns` | full, java-python |
| G5 | ✅ `forge-perl-security` | `perl-security` | full, java-python |
| G5 | ✅ `forge-perl-testing` | `perl-testing` | full, java-python |
| G5 | ✅ `forge-bun-runtime` | `bun-runtime` | full, java-python |
| G5 | ✅ `forge-compose-multiplatform-patterns` | `compose-multiplatform-patterns` | full, java-python |
| G5 | ⬜ `forge-quarkus-patterns` | `quarkus-patterns` | full |
| G5 | ⬜ `forge-quarkus-security` | `quarkus-security` | full |
| G5 | ⬜ `forge-quarkus-tdd` | `quarkus-tdd` | full |
| G5 | ⬜ `forge-quarkus-verification` | `quarkus-verification` | full |
| G5 | ⬜ `forge-laravel-patterns` | `laravel-patterns` | full |
| G5 | ⬜ `forge-laravel-security` | `laravel-security` | full |
| G5 | ⬜ `forge-laravel-tdd` | `laravel-tdd` | full |
| G5 | ⬜ `forge-laravel-verification` | `laravel-verification` | full |
| G5 | ⬜ `forge-rails-patterns` | `rails-patterns` | full |
| G5 | ⬜ `forge-dotnet-patterns` | `dotnet-patterns` | full |
| G5 | ✅ `forge-nestjs-patterns` | `nestjs-patterns` | full, java-python |
| G6 | ✅ `forge-postgres-patterns` | `postgres-patterns` | full, java-python, lite |
| G6 | ✅ `forge-mysql-patterns` | `mysql-patterns` | full, java-python, lite |
| G6 | ✅ `forge-redis-patterns` | `redis-patterns` | full, java-python, lite |
| G6 | ✅ `forge-prisma-patterns` | `prisma-patterns` | full, java-python |
| G6 | ⬜ `forge-clickhouse-io` | `clickhouse-io` | full |
| G6 | ✅ `forge-database-migrations` | `database-migrations` | full, java-python, lite |
| G6 | ⬜ `forge-data-throughput-accelerator` | `data-throughput-accelerator` | full |
| G7 | ✅ `forge-react-patterns` | `react-patterns` | full, java-python |
| G7 | ✅ `forge-react-testing` | `react-testing` | full, java-python |
| G7 | ⬜ `forge-react-performance` | `react-performance` | full |
| G7 | ✅ `forge-nextjs-turbopack` | `nextjs-turbopack` | full, java-python |
| G7 | ✅ `forge-vue-patterns` | `vue-patterns` | full, java-python |
| G7 | ✅ `forge-vite-patterns` | `vite-patterns` | full, java-python |
| G7 | ⬜ `forge-nuxt4-patterns` | `nuxt4-patterns` | full |
| G7 | ⬜ `forge-frontend-patterns` | `frontend-patterns` | full |
| G7 | ⬜ `forge-frontend-a11y` | `frontend-a11y` | full |
| G7 | ⬜ `forge-accessibility` | `accessibility` | full |
| G7 | ⬜ `forge-angular-developer` | `angular-developer` | full |
| G8 | ⬜ `forge-android-clean-architecture` | `android-clean-architecture` | full |
| G8 | ⬜ `forge-dart-flutter-patterns` | `dart-flutter-patterns` | full |
| G8 | ⬜ `forge-flutter-dart-code-review` | `flutter-dart-code-review` | full |
| G8 | ⬜ `forge-swiftui-patterns` | `swiftui-patterns` | full |
| G8 | ⬜ `forge-swift-concurrency-6-2` | `swift-concurrency-6-2` | full |
| G8 | ⬜ `forge-swift-actor-persistence` | `swift-actor-persistence` | full |
| G8 | ⬜ `forge-swift-protocol-di-testing` | `swift-protocol-di-testing` | full |
| G8 | ⬜ `forge-react-native-patterns` | `react-native-patterns` | full |
| G8 | ⬜ `forge-typescript-patterns` | `typescript-patterns` | full |
| G9 | ⬜ `forge-agent-architecture-audit` | `agent-architecture-audit` | full |
| G9 | ⬜ `forge-agent-harness-construction` | `agent-harness-construction` | full |
| G9 | ⬜ `forge-agent-introspection-debugging` | `agent-introspection-debugging` | full |
| G9 | ⬜ `forge-agent-security-hardening` | `agent-security-hardening` | full |
| G9 | ⬜ `forge-agent-self-evaluation` | `agent-self-evaluation` | full |
| G9 | ⬜ `forge-agent-eval` | `agent-eval` | full |
| G9 | ⬜ `forge-agentic-engineering` | `agentic-engineering` | full |
| G9 | ⬜ `forge-ai-first-engineering` | `ai-first-engineering` | full |
| G9 | ⬜ `forge-cost-aware-llm-pipeline` | `cost-aware-llm-pipeline` | full |
| G9 | ⬜ `forge-foundation-models-on-device` | `foundation-models-on-device` | full |
| G9 | ⬜ `forge-ml-adoption-playbook` | `ml-adoption-playbook` | full |
| G9 | ⬜ `forge-mle-workflow` | `mle-workflow` | full |
| G9 | ⬜ `forge-pytorch-patterns` | `pytorch-patterns` | full |
| G9 | ⬜ `forge-bengali-nlp` | `bengali-nlp` | full |
| G9 | ⬜ `forge-module-governance` | `module-governance` | full |
| G10 | ⬜ `forge-design-system` | `design-system` | full |
| G10 | ⬜ `forge-motion-advanced` | `motion-advanced` | full |
| G10 | ⬜ `forge-motion-foundations` | `motion-foundations` | full |
| G10 | ⬜ `forge-motion-patterns` | `motion-patterns` | full |
| G10 | ⬜ `forge-make-interfaces-feel-better` | `make-interfaces-feel-better` | full |
| G10 | ⬜ `forge-liquid-glass-design` | `liquid-glass-design` | full |
| G10 | ⬜ `forge-click-path-audit` | `click-path-audit` | full |
| G10 | ⬜ `forge-blueprint` | `blueprint` | — |
| G10 | ⬜ `forge-dev-team` | `dev-team` | full |
| G10 | ⬜ `forge-ecc-council` | `ecc-council` | full |
| G10 | ⬜ `forge-product-capability` | `product-capability` | full |
| G10 | ⬜ `forge-product-lens` | `product-lens` | full |
| 收纳 | ✅ `forge-correct` | `correct` | full, java-python |
| 收纳 | ✅ `forge-sharpen` | `sharpen` | full, java-python |
| 收纳 | ✅ `forge-engineering-principles` | `engineering-principles` | full, java-python |
| 收纳 | ✅ `forge-constraint-driven-development` | `constraint-driven-development` | full, java-python |
| 收纳 | ⬜ `forge-statechart` | `statechart` | full |
| 收纳 | ✅ `forge-qa` | `qa` | full, java-python |
| 收纳 | ✅ `forge-requirement-analysis` | `requirement-analysis` | full, java-python |
| 收纳 | ✅ `forge-test-strategy` | `test-strategy` | full, java-python |
| 收纳 | ✅ `forge-test-case-writing` | `test-case-writing` | full, java-python |
| 收纳 | ✅ `forge-test-case-review` | `test-case-review` | full, java-python |
| 收纳 | ✅ `forge-exploratory-testing` | `exploratory-testing` | full, java-python |
| 收纳 | ✅ `forge-automated-e2e-testing` | `automated-e2e-testing` | full, java-python |
| 收纳 | ✅ `forge-api-testing` | `api-testing` | full, java-python |
| 收纳 | ✅ `forge-bug-analysis` | `bug-analysis` | full, java-python |
| 收纳 | ✅ `forge-regression-testing` | `regression-testing` | full, java-python |
| 收纳 | ✅ `forge-test-reliability` | `test-reliability` | full, java-python |
| 收纳 | ✅ `forge-core` | `core` | full, java-python |
| 收纳 | ✅ `forge-qa-memory` | `qa-memory` | full, java-python |

## Commands

本 fork 不发布这类资产。上游快照仍保留在 `pool/` 里（供回溯与日后恢复），但不物化、不发布。


## Agents

| 组 | 名称（运行名） | 上游名 | 生效 profile |
| --- | --- | --- | --- |
| A1 | ⬜ `forge-code-reviewer` | `code-reviewer` | — |
| A1 | ⬜ `forge-commit-reviewer` | `commit-reviewer` | — |
| A1 | ⬜ `forge-pr-test-analyzer` | `pr-test-analyzer` | — |
| A1 | ✅ `forge-comment-analyzer` | `comment-analyzer` | full, java-python |
| A1 | ✅ `forge-silent-failure-hunter` | `silent-failure-hunter` | full, java-python, lite |
| A1 | ✅ `forge-type-design-analyzer` | `type-design-analyzer` | full, java-python |
| A1 | ⬜ `forge-security-reviewer` | `security-reviewer` | — |
| A1 | ✅ `forge-code-simplifier` | `code-simplifier` | full, java-python, lite |
| A1 | ✅ `forge-refactor-cleaner` | `refactor-cleaner` | full, java-python, lite |
| A2 | ✅ `forge-architect` | `architect` | full, java-python |
| A2 | ⬜ `forge-code-architect` | `code-architect` | — |
| A2 | ⬜ `forge-code-explorer` | `code-explorer` | — |
| A2 | ⬜ `forge-planner` | `planner` | — |
| A2 | ✅ `forge-build-error-resolver` | `build-error-resolver` | full, java-python |
| A2 | ✅ `forge-performance-optimizer` | `performance-optimizer` | full, java-python |
| A2 | ⬜ `forge-tdd-guide` | `tdd-guide` | — |
| A2 | ✅ `forge-e2e-runner` | `e2e-runner` | full, java-python |
| A2 | ⬜ `forge-spec-miner` | `spec-miner` | — |
| A3 | ✅ `forge-java-reviewer` | `java-reviewer` | full, java-python, lite |
| A3 | ✅ `forge-java-build-resolver` | `java-build-resolver` | full, java-python, lite |
| A3 | ✅ `forge-kotlin-reviewer` | `kotlin-reviewer` | full, java-python, lite |
| A3 | ✅ `forge-kotlin-build-resolver` | `kotlin-build-resolver` | full, java-python, lite |
| A4 | ✅ `forge-python-reviewer` | `python-reviewer` | full, java-python, lite |
| A4 | ✅ `forge-django-reviewer` | `django-reviewer` | full, java-python, lite |
| A4 | ✅ `forge-django-build-resolver` | `django-build-resolver` | full, java-python, lite |
| A4 | ✅ `forge-fastapi-reviewer` | `fastapi-reviewer` | full, java-python, lite |
| A5 | ⬜ `forge-typescript-reviewer` | `typescript-reviewer` | full |
| A5 | ⬜ `forge-react-reviewer` | `react-reviewer` | full |
| A5 | ⬜ `forge-react-build-resolver` | `react-build-resolver` | full |
| A5 | ⬜ `forge-vue-reviewer` | `vue-reviewer` | full |
| A6 | ⬜ `forge-go-reviewer` | `go-reviewer` | full |
| A6 | ⬜ `forge-go-build-resolver` | `go-build-resolver` | full |
| A6 | ⬜ `forge-rust-reviewer` | `rust-reviewer` | full |
| A6 | ⬜ `forge-rust-build-resolver` | `rust-build-resolver` | full |
| A6 | ⬜ `forge-cpp-reviewer` | `cpp-reviewer` | full |
| A6 | ⬜ `forge-cpp-build-resolver` | `cpp-build-resolver` | full |
| A6 | ⬜ `forge-csharp-reviewer` | `csharp-reviewer` | full |
| A6 | ⬜ `forge-php-reviewer` | `php-reviewer` | full |
| A6 | ⬜ `forge-ruby-reviewer` | `ruby-reviewer` | full |
| A6 | ⬜ `forge-swift-reviewer` | `swift-reviewer` | full |
| A6 | ⬜ `forge-swift-build-resolver` | `swift-build-resolver` | full |
| A6 | ⬜ `forge-dart-build-resolver` | `dart-build-resolver` | full |
| A6 | ⬜ `forge-flutter-reviewer` | `flutter-reviewer` | full |
| A6 | ⬜ `forge-fsharp-reviewer` | `fsharp-reviewer` | full |
| A6 | ⬜ `forge-harmonyos-app-resolver` | `harmonyos-app-resolver` | full |
| A6 | ⬜ `forge-pytorch-build-resolver` | `pytorch-build-resolver` | full |
| A7 | ✅ `forge-database-reviewer` | `database-reviewer` | full, java-python |
| A7 | ✅ `forge-network-architect` | `network-architect` | full, java-python |
| A7 | ✅ `forge-network-config-reviewer` | `network-config-reviewer` | full, java-python |
| A7 | ✅ `forge-network-troubleshooter` | `network-troubleshooter` | full, java-python |
| A7 | ✅ `forge-homelab-architect` | `homelab-architect` | full, java-python |
| A7 | ⬜ `forge-rag-pipeline-reviewer` | `rag-pipeline-reviewer` | full |
| A7 | ⬜ `forge-mle-reviewer` | `mle-reviewer` | full |
| A8 | ⬜ `forge-doc-updater` | `doc-updater` | full |
| A8 | ⬜ `forge-docs-lookup` | `docs-lookup` | full |
| A8 | ⬜ `forge-opensource-forker` | `opensource-forker` | full |
| A8 | ⬜ `forge-opensource-packager` | `opensource-packager` | full |
| A8 | ⬜ `forge-opensource-sanitizer` | `opensource-sanitizer` | full |
| A9 | ⬜ `forge-a11y-architect` | `a11y-architect` | — |
| A9 | ⬜ `forge-bengali-reviewer` | `bengali-reviewer` | — |
| A9 | ⬜ `forge-healthcare-reviewer` | `healthcare-reviewer` | — |
| A9 | ⬜ `forge-chief-of-staff` | `chief-of-staff` | — |
| A9 | ⬜ `forge-marketing-agent` | `marketing-agent` | — |
| A9 | ⬜ `forge-seo-specialist` | `seo-specialist` | — |
| A9 | ⬜ `forge-conversation-analyzer` | `conversation-analyzer` | — |
| A9 | ⬜ `forge-agent-evaluator` | `agent-evaluator` | — |
| A9 | ⬜ `forge-harness-optimizer` | `harness-optimizer` | — |
| A9 | ⬜ `forge-loop-operator` | `loop-operator` | — |
| A10 | ⬜ `forge-gan-planner` | `gan-planner` | — |
| A10 | ⬜ `forge-gan-generator` | `gan-generator` | — |
| A10 | ⬜ `forge-gan-evaluator` | `gan-evaluator` | — |

## fork 自有资产

- skill：`forge-absorb-third-party-skill`（把第三方仓库的 skill 收纳进 absorbed 池）
- skill：`forge-ci-triage`（本插件 CI 失败定位：日志分组读、本地三 profile 复现、门禁分工）
- skill：`forge-incident-response`（事故响应：定级、止血、复盘）
- skill：`forge-observability`（可观测性：日志 / 指标 / 追踪、SLO、告警）
- skill：`forge-pipeline`（本插件的更新与发布流水线：门禁顺序、profile 规模、Windows 坑）
- skill：`forge-release-management`（发布：tag、changelog、分级发布与回滚）
- skill：`forge-router`（选路表：任务 → skill / agent 组合）
- rules：`omp-tooling` `omp-delegation` `fork-workflow` `fork-verification` `fork-coding-style`
