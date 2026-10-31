# ECC-OMP-Fork 资产目录

> 由 `tools/build_catalog.py` 生成，勿手改。
> 上游：[affaan-m/ECC](https://github.com/affaan-m/ECC)（MIT）。

当前生效 profile：**java-python**。

| profile | 说明 | skills | commands | agents |
| --- | --- | --- | --- | --- |
| `full` | 上游 pi/core 全量技能（去掉与其它插件重复的 5 个）加编程相关 agent。不含命令。token 开销最大，仅在需要冷门技术栈时用。 | 127 | 0 | 49 |
| `java-python` | Java/Kotlin + Python/Django/FastAPI 主力 + 通用工程规范。面向后端/测试开发日常。 | 65 | 0 | 22 |
| `lite` | 最小可用集：只保留后端核心规范 + Java/Python 主力 + 通用评审 agent。每轮提示开销最低。 | 39 | 0 | 11 |

> 表里的**运行名**是本 fork 物化后实际使用的名字：上游名统一加 `ecc-omp-` 前缀（skill / command / agent）。
> 「上游名」是 affaan-m/ECC 里的名称，用于回溯上游来源。

## Skills

| 组 | 名称（运行名） | 上游名 | 生效 profile |
| --- | --- | --- | --- |
| G1 | ✅ `ecc-omp-api-design` | `api-design` | full, java-python, lite |
| G1 | ✅ `ecc-omp-backend-patterns` | `backend-patterns` | full, java-python, lite |
| G1 | ✅ `ecc-omp-hexagonal-architecture` | `hexagonal-architecture` | full, java-python, lite |
| G1 | ⬜ `ecc-omp-architecture-decision-records` | `architecture-decision-records` | — |
| G1 | ✅ `ecc-omp-contract-first` | `contract-first` | full, java-python, lite |
| G1 | ⬜ `ecc-omp-api-connector-builder` | `api-connector-builder` | full |
| G1 | ✅ `ecc-omp-content-hash-cache-pattern` | `content-hash-cache-pattern` | full, java-python |
| G1 | ✅ `ecc-omp-regex-vs-llm-structured-text` | `regex-vs-llm-structured-text` | full, java-python, lite |
| G1 | ⬜ `ecc-omp-mcp-server-patterns` | `mcp-server-patterns` | full |
| G2 | ✅ `ecc-omp-coding-standards` | `coding-standards` | full, java-python, lite |
| G2 | ✅ `ecc-omp-error-handling` | `error-handling` | full, java-python, lite |
| G2 | ⬜ `ecc-omp-intent-driven-development` | `intent-driven-development` | — |
| G2 | ✅ `ecc-omp-change-impact` | `change-impact` | full, java-python, lite |
| G2 | ⬜ `ecc-omp-context-and-decisions` | `context-and-decisions` | — |
| G2 | ✅ `ecc-omp-inherit-legacy-style` | `inherit-legacy-style` | full, java-python, lite |
| G2 | ✅ `ecc-omp-code-tour` | `code-tour` | full, java-python, lite |
| G2 | ✅ `ecc-omp-codebase-onboarding` | `codebase-onboarding` | full, java-python, lite |
| G2 | ✅ `ecc-omp-conventional-commit-review` | `conventional-commit-review` | full, java-python, lite |
| G2 | ✅ `ecc-omp-git-workflow` | `git-workflow` | full, java-python, lite |
| G2 | ✅ `ecc-omp-docs-governance` | `docs-governance` | full, java-python, lite |
| G2 | ⬜ `ecc-omp-living-docs-governance` | `living-docs-governance` | full |
| G2 | ✅ `ecc-omp-security-review` | `security-review` | full, java-python, lite |
| G2 | ⬜ `ecc-omp-tdd-workflow` | `tdd-workflow` | — |
| G2 | ✅ `ecc-omp-test-collaboration` | `test-collaboration` | full, java-python, lite |
| G2 | ✅ `ecc-omp-verification-loop` | `verification-loop` | full, java-python, lite |
| G2 | ⬜ `ecc-omp-module-regression` | `module-regression` | full |
| G2 | ✅ `ecc-omp-e2e-testing` | `e2e-testing` | full, java-python, lite |
| G2 | ✅ `ecc-omp-production-audit` | `production-audit` | full, java-python |
| G2 | ⬜ `ecc-omp-parallel-execution-optimizer` | `parallel-execution-optimizer` | full |
| G2 | ⬜ `ecc-omp-benchmark` | `benchmark` | full |
| G2 | ⬜ `ecc-omp-benchmark-optimization-loop` | `benchmark-optimization-loop` | full |
| G2 | ⬜ `ecc-omp-latency-critical-systems` | `latency-critical-systems` | full |
| G2 | ✅ `ecc-omp-deployment-patterns` | `deployment-patterns` | full, java-python, lite |
| G2 | ✅ `ecc-omp-docker-patterns` | `docker-patterns` | full, java-python, lite |
| G2 | ✅ `ecc-omp-kubernetes-patterns` | `kubernetes-patterns` | full, java-python, lite |
| G2 | ✅ `ecc-omp-dashboard-builder` | `dashboard-builder` | full, java-python |
| G3 | ✅ `ecc-omp-java-coding-standards` | `java-coding-standards` | full, java-python, lite |
| G3 | ✅ `ecc-omp-springboot-patterns` | `springboot-patterns` | full, java-python, lite |
| G3 | ✅ `ecc-omp-springboot-security` | `springboot-security` | full, java-python, lite |
| G3 | ✅ `ecc-omp-springboot-tdd` | `springboot-tdd` | full, java-python, lite |
| G3 | ✅ `ecc-omp-springboot-verification` | `springboot-verification` | full, java-python, lite |
| G3 | ✅ `ecc-omp-jpa-patterns` | `jpa-patterns` | full, java-python |
| G3 | ✅ `ecc-omp-mybatis-patterns` | `mybatis-patterns` | full, java-python |
| G3 | ✅ `ecc-omp-kotlin-patterns` | `kotlin-patterns` | full, java-python, lite |
| G3 | ✅ `ecc-omp-kotlin-testing` | `kotlin-testing` | full, java-python, lite |
| G3 | ⬜ `ecc-omp-kotlin-coroutines-flows` | `kotlin-coroutines-flows` | full |
| G3 | ⬜ `ecc-omp-kotlin-exposed-patterns` | `kotlin-exposed-patterns` | full |
| G3 | ⬜ `ecc-omp-kotlin-ktor-patterns` | `kotlin-ktor-patterns` | full |
| G4 | ✅ `ecc-omp-python-patterns` | `python-patterns` | full, java-python, lite |
| G4 | ✅ `ecc-omp-python-testing` | `python-testing` | full, java-python, lite |
| G4 | ✅ `ecc-omp-django-patterns` | `django-patterns` | full, java-python, lite |
| G4 | ✅ `ecc-omp-django-tdd` | `django-tdd` | full, java-python, lite |
| G4 | ✅ `ecc-omp-django-verification` | `django-verification` | full, java-python, lite |
| G4 | ✅ `ecc-omp-django-security` | `django-security` | full, java-python, lite |
| G4 | ✅ `ecc-omp-django-celery` | `django-celery` | full, java-python |
| G4 | ✅ `ecc-omp-fastapi-patterns` | `fastapi-patterns` | full, java-python, lite |
| G5 | ✅ `ecc-omp-golang-patterns` | `golang-patterns` | full, java-python |
| G5 | ✅ `ecc-omp-golang-testing` | `golang-testing` | full, java-python |
| G5 | ✅ `ecc-omp-rust-patterns` | `rust-patterns` | full, java-python |
| G5 | ✅ `ecc-omp-rust-testing` | `rust-testing` | full, java-python |
| G5 | ✅ `ecc-omp-cpp-coding-standards` | `cpp-coding-standards` | full, java-python |
| G5 | ✅ `ecc-omp-cpp-testing` | `cpp-testing` | full, java-python |
| G5 | ✅ `ecc-omp-csharp-testing` | `csharp-testing` | full, java-python |
| G5 | ✅ `ecc-omp-fsharp-testing` | `fsharp-testing` | full, java-python |
| G5 | ✅ `ecc-omp-perl-patterns` | `perl-patterns` | full, java-python |
| G5 | ✅ `ecc-omp-perl-security` | `perl-security` | full, java-python |
| G5 | ✅ `ecc-omp-perl-testing` | `perl-testing` | full, java-python |
| G5 | ✅ `ecc-omp-bun-runtime` | `bun-runtime` | full, java-python |
| G5 | ✅ `ecc-omp-compose-multiplatform-patterns` | `compose-multiplatform-patterns` | full, java-python |
| G5 | ⬜ `ecc-omp-quarkus-patterns` | `quarkus-patterns` | full |
| G5 | ⬜ `ecc-omp-quarkus-security` | `quarkus-security` | full |
| G5 | ⬜ `ecc-omp-quarkus-tdd` | `quarkus-tdd` | full |
| G5 | ⬜ `ecc-omp-quarkus-verification` | `quarkus-verification` | full |
| G5 | ⬜ `ecc-omp-laravel-patterns` | `laravel-patterns` | full |
| G5 | ⬜ `ecc-omp-laravel-security` | `laravel-security` | full |
| G5 | ⬜ `ecc-omp-laravel-tdd` | `laravel-tdd` | full |
| G5 | ⬜ `ecc-omp-laravel-verification` | `laravel-verification` | full |
| G5 | ⬜ `ecc-omp-rails-patterns` | `rails-patterns` | full |
| G5 | ⬜ `ecc-omp-dotnet-patterns` | `dotnet-patterns` | full |
| G5 | ✅ `ecc-omp-nestjs-patterns` | `nestjs-patterns` | full, java-python |
| G6 | ✅ `ecc-omp-postgres-patterns` | `postgres-patterns` | full, java-python, lite |
| G6 | ✅ `ecc-omp-mysql-patterns` | `mysql-patterns` | full, java-python, lite |
| G6 | ✅ `ecc-omp-redis-patterns` | `redis-patterns` | full, java-python, lite |
| G6 | ✅ `ecc-omp-prisma-patterns` | `prisma-patterns` | full, java-python |
| G6 | ⬜ `ecc-omp-clickhouse-io` | `clickhouse-io` | full |
| G6 | ✅ `ecc-omp-database-migrations` | `database-migrations` | full, java-python, lite |
| G6 | ⬜ `ecc-omp-data-throughput-accelerator` | `data-throughput-accelerator` | full |
| G7 | ✅ `ecc-omp-react-patterns` | `react-patterns` | full, java-python |
| G7 | ✅ `ecc-omp-react-testing` | `react-testing` | full, java-python |
| G7 | ⬜ `ecc-omp-react-performance` | `react-performance` | full |
| G7 | ✅ `ecc-omp-nextjs-turbopack` | `nextjs-turbopack` | full, java-python |
| G7 | ✅ `ecc-omp-vue-patterns` | `vue-patterns` | full, java-python |
| G7 | ✅ `ecc-omp-vite-patterns` | `vite-patterns` | full, java-python |
| G7 | ⬜ `ecc-omp-nuxt4-patterns` | `nuxt4-patterns` | full |
| G7 | ⬜ `ecc-omp-frontend-patterns` | `frontend-patterns` | full |
| G7 | ⬜ `ecc-omp-frontend-a11y` | `frontend-a11y` | full |
| G7 | ⬜ `ecc-omp-accessibility` | `accessibility` | full |
| G7 | ⬜ `ecc-omp-angular-developer` | `angular-developer` | full |
| G8 | ⬜ `ecc-omp-android-clean-architecture` | `android-clean-architecture` | full |
| G8 | ⬜ `ecc-omp-dart-flutter-patterns` | `dart-flutter-patterns` | full |
| G8 | ⬜ `ecc-omp-flutter-dart-code-review` | `flutter-dart-code-review` | full |
| G8 | ⬜ `ecc-omp-swiftui-patterns` | `swiftui-patterns` | full |
| G8 | ⬜ `ecc-omp-swift-concurrency-6-2` | `swift-concurrency-6-2` | full |
| G8 | ⬜ `ecc-omp-swift-actor-persistence` | `swift-actor-persistence` | full |
| G8 | ⬜ `ecc-omp-swift-protocol-di-testing` | `swift-protocol-di-testing` | full |
| G8 | ⬜ `ecc-omp-react-native-patterns` | `react-native-patterns` | full |
| G9 | ⬜ `ecc-omp-agent-architecture-audit` | `agent-architecture-audit` | full |
| G9 | ⬜ `ecc-omp-agent-harness-construction` | `agent-harness-construction` | full |
| G9 | ⬜ `ecc-omp-agent-introspection-debugging` | `agent-introspection-debugging` | full |
| G9 | ⬜ `ecc-omp-agent-security-hardening` | `agent-security-hardening` | full |
| G9 | ⬜ `ecc-omp-agent-self-evaluation` | `agent-self-evaluation` | full |
| G9 | ⬜ `ecc-omp-agent-eval` | `agent-eval` | full |
| G9 | ⬜ `ecc-omp-agentic-engineering` | `agentic-engineering` | full |
| G9 | ⬜ `ecc-omp-ai-first-engineering` | `ai-first-engineering` | full |
| G9 | ⬜ `ecc-omp-cost-aware-llm-pipeline` | `cost-aware-llm-pipeline` | full |
| G9 | ⬜ `ecc-omp-foundation-models-on-device` | `foundation-models-on-device` | full |
| G9 | ⬜ `ecc-omp-ml-adoption-playbook` | `ml-adoption-playbook` | full |
| G9 | ⬜ `ecc-omp-mle-workflow` | `mle-workflow` | full |
| G9 | ⬜ `ecc-omp-pytorch-patterns` | `pytorch-patterns` | full |
| G9 | ⬜ `ecc-omp-bengali-nlp` | `bengali-nlp` | full |
| G10 | ⬜ `ecc-omp-design-system` | `design-system` | full |
| G10 | ⬜ `ecc-omp-motion-advanced` | `motion-advanced` | full |
| G10 | ⬜ `ecc-omp-motion-foundations` | `motion-foundations` | full |
| G10 | ⬜ `ecc-omp-motion-patterns` | `motion-patterns` | full |
| G10 | ⬜ `ecc-omp-make-interfaces-feel-better` | `make-interfaces-feel-better` | full |
| G10 | ⬜ `ecc-omp-liquid-glass-design` | `liquid-glass-design` | full |
| G10 | ⬜ `ecc-omp-click-path-audit` | `click-path-audit` | full |
| G10 | ⬜ `ecc-omp-blueprint` | `blueprint` | — |
| G10 | ⬜ `ecc-omp-dev-team` | `dev-team` | full |
| G10 | ⬜ `ecc-omp-ecc-council` | `ecc-council` | full |
| G10 | ⬜ `ecc-omp-product-capability` | `product-capability` | full |
| G10 | ⬜ `ecc-omp-product-lens` | `product-lens` | full |

## Commands

本 fork 不发布这类资产。上游快照仍保留在 `pool/` 里（供回溯与日后恢复），但不物化、不发布。


## Agents

| 组 | 名称（运行名） | 上游名 | 生效 profile |
| --- | --- | --- | --- |
| A1 | ⬜ `ecc-omp-code-reviewer` | `code-reviewer` | — |
| A1 | ⬜ `ecc-omp-commit-reviewer` | `commit-reviewer` | — |
| A1 | ⬜ `ecc-omp-pr-test-analyzer` | `pr-test-analyzer` | — |
| A1 | ✅ `ecc-omp-comment-analyzer` | `comment-analyzer` | full, java-python |
| A1 | ✅ `ecc-omp-silent-failure-hunter` | `silent-failure-hunter` | full, java-python, lite |
| A1 | ✅ `ecc-omp-type-design-analyzer` | `type-design-analyzer` | full, java-python |
| A1 | ⬜ `ecc-omp-security-reviewer` | `security-reviewer` | — |
| A1 | ✅ `ecc-omp-code-simplifier` | `code-simplifier` | full, java-python, lite |
| A1 | ✅ `ecc-omp-refactor-cleaner` | `refactor-cleaner` | full, java-python, lite |
| A2 | ✅ `ecc-omp-architect` | `architect` | full, java-python |
| A2 | ⬜ `ecc-omp-code-architect` | `code-architect` | — |
| A2 | ⬜ `ecc-omp-code-explorer` | `code-explorer` | — |
| A2 | ⬜ `ecc-omp-planner` | `planner` | — |
| A2 | ✅ `ecc-omp-build-error-resolver` | `build-error-resolver` | full, java-python |
| A2 | ✅ `ecc-omp-performance-optimizer` | `performance-optimizer` | full, java-python |
| A2 | ⬜ `ecc-omp-tdd-guide` | `tdd-guide` | — |
| A2 | ✅ `ecc-omp-e2e-runner` | `e2e-runner` | full, java-python |
| A2 | ⬜ `ecc-omp-spec-miner` | `spec-miner` | — |
| A3 | ✅ `ecc-omp-java-reviewer` | `java-reviewer` | full, java-python, lite |
| A3 | ✅ `ecc-omp-java-build-resolver` | `java-build-resolver` | full, java-python, lite |
| A3 | ✅ `ecc-omp-kotlin-reviewer` | `kotlin-reviewer` | full, java-python, lite |
| A3 | ✅ `ecc-omp-kotlin-build-resolver` | `kotlin-build-resolver` | full, java-python, lite |
| A4 | ✅ `ecc-omp-python-reviewer` | `python-reviewer` | full, java-python, lite |
| A4 | ✅ `ecc-omp-django-reviewer` | `django-reviewer` | full, java-python, lite |
| A4 | ✅ `ecc-omp-django-build-resolver` | `django-build-resolver` | full, java-python, lite |
| A4 | ✅ `ecc-omp-fastapi-reviewer` | `fastapi-reviewer` | full, java-python, lite |
| A5 | ⬜ `ecc-omp-typescript-reviewer` | `typescript-reviewer` | full |
| A5 | ⬜ `ecc-omp-react-reviewer` | `react-reviewer` | full |
| A5 | ⬜ `ecc-omp-react-build-resolver` | `react-build-resolver` | full |
| A5 | ⬜ `ecc-omp-vue-reviewer` | `vue-reviewer` | full |
| A6 | ⬜ `ecc-omp-go-reviewer` | `go-reviewer` | full |
| A6 | ⬜ `ecc-omp-go-build-resolver` | `go-build-resolver` | full |
| A6 | ⬜ `ecc-omp-rust-reviewer` | `rust-reviewer` | full |
| A6 | ⬜ `ecc-omp-rust-build-resolver` | `rust-build-resolver` | full |
| A6 | ⬜ `ecc-omp-cpp-reviewer` | `cpp-reviewer` | full |
| A6 | ⬜ `ecc-omp-cpp-build-resolver` | `cpp-build-resolver` | full |
| A6 | ⬜ `ecc-omp-csharp-reviewer` | `csharp-reviewer` | full |
| A6 | ⬜ `ecc-omp-php-reviewer` | `php-reviewer` | full |
| A6 | ⬜ `ecc-omp-ruby-reviewer` | `ruby-reviewer` | full |
| A6 | ⬜ `ecc-omp-swift-reviewer` | `swift-reviewer` | full |
| A6 | ⬜ `ecc-omp-swift-build-resolver` | `swift-build-resolver` | full |
| A6 | ⬜ `ecc-omp-dart-build-resolver` | `dart-build-resolver` | full |
| A6 | ⬜ `ecc-omp-flutter-reviewer` | `flutter-reviewer` | full |
| A6 | ⬜ `ecc-omp-fsharp-reviewer` | `fsharp-reviewer` | full |
| A6 | ⬜ `ecc-omp-harmonyos-app-resolver` | `harmonyos-app-resolver` | full |
| A6 | ⬜ `ecc-omp-pytorch-build-resolver` | `pytorch-build-resolver` | full |
| A7 | ✅ `ecc-omp-database-reviewer` | `database-reviewer` | full, java-python |
| A7 | ✅ `ecc-omp-network-architect` | `network-architect` | full, java-python |
| A7 | ✅ `ecc-omp-network-config-reviewer` | `network-config-reviewer` | full, java-python |
| A7 | ✅ `ecc-omp-network-troubleshooter` | `network-troubleshooter` | full, java-python |
| A7 | ✅ `ecc-omp-homelab-architect` | `homelab-architect` | full, java-python |
| A7 | ⬜ `ecc-omp-rag-pipeline-reviewer` | `rag-pipeline-reviewer` | full |
| A7 | ⬜ `ecc-omp-mle-reviewer` | `mle-reviewer` | full |
| A8 | ⬜ `ecc-omp-doc-updater` | `doc-updater` | full |
| A8 | ⬜ `ecc-omp-docs-lookup` | `docs-lookup` | full |
| A8 | ⬜ `ecc-omp-opensource-forker` | `opensource-forker` | full |
| A8 | ⬜ `ecc-omp-opensource-packager` | `opensource-packager` | full |
| A8 | ⬜ `ecc-omp-opensource-sanitizer` | `opensource-sanitizer` | full |
| A9 | ⬜ `ecc-omp-a11y-architect` | `a11y-architect` | — |
| A9 | ⬜ `ecc-omp-bengali-reviewer` | `bengali-reviewer` | — |
| A9 | ⬜ `ecc-omp-healthcare-reviewer` | `healthcare-reviewer` | — |
| A9 | ⬜ `ecc-omp-chief-of-staff` | `chief-of-staff` | — |
| A9 | ⬜ `ecc-omp-marketing-agent` | `marketing-agent` | — |
| A9 | ⬜ `ecc-omp-seo-specialist` | `seo-specialist` | — |
| A9 | ⬜ `ecc-omp-conversation-analyzer` | `conversation-analyzer` | — |
| A9 | ⬜ `ecc-omp-agent-evaluator` | `agent-evaluator` | — |
| A9 | ⬜ `ecc-omp-harness-optimizer` | `harness-optimizer` | — |
| A9 | ⬜ `ecc-omp-loop-operator` | `loop-operator` | — |
| A10 | ⬜ `ecc-omp-gan-planner` | `gan-planner` | — |
| A10 | ⬜ `ecc-omp-gan-generator` | `gan-generator` | — |
| A10 | ⬜ `ecc-omp-gan-evaluator` | `gan-evaluator` | — |

## fork 自有资产

- skill：`ecc-omp-router`（选路表：任务 → skill / agent 组合）
- skill：`ecc-omp-release-management`（发布：tag、changelog、分级发布与回滚）
- skill：`ecc-omp-observability`（可观测性：日志 / 指标 / 追踪、SLO、告警）
- skill：`ecc-omp-incident-response`（事故响应：定级、止血、复盘）
- rules：`omp-tooling` `omp-delegation` `fork-workflow` `fork-verification` `fork-coding-style`
