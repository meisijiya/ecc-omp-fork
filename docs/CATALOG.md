# ECC-OMP-Fork 资产目录

> 由 `tools/build_catalog.py` 生成，勿手改。
> 上游：[affaan-m/ECC](https://github.com/affaan-m/ECC)（MIT）。

当前生效 profile：**java-python**。

| profile | 说明 | skills | commands | agents |
| --- | --- | --- | --- | --- |
| `full` | 上游 pi/core 全量（132 skills + 24 commands）加编程相关 agent。token 开销最大，仅在需要冷门技术栈时用。 | 132 | 24 | 58 |
| `java-python` | Java/Kotlin + Python/Django/FastAPI 主力 + 通用工程规范。面向后端/测试开发日常。 | 67 | 24 | 31 |
| `lite` | 最小可用集：只保留后端核心规范 + Java/Python 主力 + 通用评审 agent。每轮提示开销最低。 | 43 | 15 | 14 |

## Skills

| 组 | 名称 | 生效 profile |
| --- | --- | --- |
| G1 | ✅ `api-design` | full, java-python, lite |
| G1 | ✅ `backend-patterns` | full, java-python, lite |
| G1 | ✅ `hexagonal-architecture` | full, java-python, lite |
| G1 | ✅ `architecture-decision-records` | full, java-python, lite |
| G1 | ✅ `contract-first` | full, java-python, lite |
| G1 | ⬜ `api-connector-builder` | full |
| G1 | ✅ `content-hash-cache-pattern` | full, java-python |
| G1 | ✅ `regex-vs-llm-structured-text` | full, java-python, lite |
| G1 | ⬜ `mcp-server-patterns` | full |
| G2 | ✅ `coding-standards` | full, java-python, lite |
| G2 | ✅ `error-handling` | full, java-python, lite |
| G2 | ✅ `intent-driven-development` | full, java-python, lite |
| G2 | ✅ `change-impact` | full, java-python, lite |
| G2 | ✅ `context-and-decisions` | full, java-python, lite |
| G2 | ✅ `inherit-legacy-style` | full, java-python, lite |
| G2 | ✅ `code-tour` | full, java-python, lite |
| G2 | ✅ `codebase-onboarding` | full, java-python, lite |
| G2 | ✅ `conventional-commit-review` | full, java-python, lite |
| G2 | ✅ `git-workflow` | full, java-python, lite |
| G2 | ✅ `docs-governance` | full, java-python, lite |
| G2 | ⬜ `living-docs-governance` | full |
| G2 | ✅ `security-review` | full, java-python, lite |
| G2 | ✅ `tdd-workflow` | full, java-python, lite |
| G2 | ✅ `test-collaboration` | full, java-python, lite |
| G2 | ✅ `verification-loop` | full, java-python, lite |
| G2 | ⬜ `module-regression` | full |
| G2 | ✅ `e2e-testing` | full, java-python, lite |
| G2 | ⬜ `production-audit` | full |
| G2 | ⬜ `parallel-execution-optimizer` | full |
| G2 | ⬜ `benchmark` | full |
| G2 | ⬜ `benchmark-optimization-loop` | full |
| G2 | ⬜ `latency-critical-systems` | full |
| G2 | ✅ `deployment-patterns` | full, java-python, lite |
| G2 | ✅ `docker-patterns` | full, java-python, lite |
| G2 | ✅ `kubernetes-patterns` | full, java-python, lite |
| G3 | ✅ `java-coding-standards` | full, java-python, lite |
| G3 | ✅ `springboot-patterns` | full, java-python, lite |
| G3 | ✅ `springboot-security` | full, java-python, lite |
| G3 | ✅ `springboot-tdd` | full, java-python, lite |
| G3 | ✅ `springboot-verification` | full, java-python, lite |
| G3 | ✅ `jpa-patterns` | full, java-python |
| G3 | ✅ `mybatis-patterns` | full, java-python |
| G3 | ✅ `kotlin-patterns` | full, java-python, lite |
| G3 | ✅ `kotlin-testing` | full, java-python, lite |
| G3 | ⬜ `kotlin-coroutines-flows` | full |
| G3 | ⬜ `kotlin-exposed-patterns` | full |
| G3 | ⬜ `kotlin-ktor-patterns` | full |
| G4 | ✅ `python-patterns` | full, java-python, lite |
| G4 | ✅ `python-testing` | full, java-python, lite |
| G4 | ✅ `django-patterns` | full, java-python, lite |
| G4 | ✅ `django-tdd` | full, java-python, lite |
| G4 | ✅ `django-verification` | full, java-python, lite |
| G4 | ✅ `django-security` | full, java-python, lite |
| G4 | ✅ `django-celery` | full, java-python |
| G4 | ✅ `fastapi-patterns` | full, java-python, lite |
| G5 | ✅ `golang-patterns` | full, java-python |
| G5 | ✅ `golang-testing` | full, java-python |
| G5 | ✅ `rust-patterns` | full, java-python |
| G5 | ✅ `rust-testing` | full, java-python |
| G5 | ✅ `cpp-coding-standards` | full, java-python |
| G5 | ✅ `cpp-testing` | full, java-python |
| G5 | ✅ `csharp-testing` | full, java-python |
| G5 | ✅ `fsharp-testing` | full, java-python |
| G5 | ✅ `perl-patterns` | full, java-python |
| G5 | ✅ `perl-security` | full, java-python |
| G5 | ✅ `perl-testing` | full, java-python |
| G5 | ✅ `bun-runtime` | full, java-python |
| G5 | ✅ `compose-multiplatform-patterns` | full, java-python |
| G5 | ⬜ `quarkus-patterns` | full |
| G5 | ⬜ `quarkus-security` | full |
| G5 | ⬜ `quarkus-tdd` | full |
| G5 | ⬜ `quarkus-verification` | full |
| G5 | ⬜ `laravel-patterns` | full |
| G5 | ⬜ `laravel-security` | full |
| G5 | ⬜ `laravel-tdd` | full |
| G5 | ⬜ `laravel-verification` | full |
| G5 | ⬜ `rails-patterns` | full |
| G5 | ⬜ `dotnet-patterns` | full |
| G5 | ✅ `nestjs-patterns` | full, java-python |
| G6 | ✅ `postgres-patterns` | full, java-python, lite |
| G6 | ✅ `mysql-patterns` | full, java-python, lite |
| G6 | ✅ `redis-patterns` | full, java-python, lite |
| G6 | ✅ `prisma-patterns` | full, java-python |
| G6 | ⬜ `clickhouse-io` | full |
| G6 | ✅ `database-migrations` | full, java-python, lite |
| G6 | ⬜ `data-throughput-accelerator` | full |
| G7 | ✅ `react-patterns` | full, java-python |
| G7 | ✅ `react-testing` | full, java-python |
| G7 | ⬜ `react-performance` | full |
| G7 | ✅ `nextjs-turbopack` | full, java-python |
| G7 | ✅ `vue-patterns` | full, java-python |
| G7 | ✅ `vite-patterns` | full, java-python |
| G7 | ⬜ `nuxt4-patterns` | full |
| G7 | ⬜ `frontend-patterns` | full |
| G7 | ⬜ `frontend-a11y` | full |
| G7 | ⬜ `accessibility` | full |
| G7 | ⬜ `angular-developer` | full |
| G8 | ⬜ `android-clean-architecture` | full |
| G8 | ⬜ `dart-flutter-patterns` | full |
| G8 | ⬜ `flutter-dart-code-review` | full |
| G8 | ⬜ `swiftui-patterns` | full |
| G8 | ⬜ `swift-concurrency-6-2` | full |
| G8 | ⬜ `swift-actor-persistence` | full |
| G8 | ⬜ `swift-protocol-di-testing` | full |
| G8 | ⬜ `react-native-patterns` | full |
| G9 | ⬜ `agent-architecture-audit` | full |
| G9 | ⬜ `agent-harness-construction` | full |
| G9 | ⬜ `agent-introspection-debugging` | full |
| G9 | ⬜ `agent-security-hardening` | full |
| G9 | ⬜ `agent-self-evaluation` | full |
| G9 | ⬜ `agent-eval` | full |
| G9 | ⬜ `agentic-engineering` | full |
| G9 | ⬜ `ai-first-engineering` | full |
| G9 | ⬜ `cost-aware-llm-pipeline` | full |
| G9 | ⬜ `foundation-models-on-device` | full |
| G9 | ⬜ `ml-adoption-playbook` | full |
| G9 | ⬜ `mle-workflow` | full |
| G9 | ⬜ `pytorch-patterns` | full |
| G9 | ⬜ `bengali-nlp` | full |
| G10 | ⬜ `design-system` | full |
| G10 | ⬜ `motion-advanced` | full |
| G10 | ⬜ `motion-foundations` | full |
| G10 | ⬜ `motion-patterns` | full |
| G10 | ⬜ `make-interfaces-feel-better` | full |
| G10 | ⬜ `liquid-glass-design` | full |
| G10 | ⬜ `click-path-audit` | full |
| G10 | ⬜ `dashboard-builder` | full |
| G10 | ⬜ `blueprint` | full |
| G10 | ⬜ `dev-team` | full |
| G10 | ⬜ `ecc-council` | full |
| G10 | ⬜ `product-capability` | full |
| G10 | ⬜ `product-lens` | full |

## Commands

| 组 | 名称 | 生效 profile |
| --- | --- | --- |
| C1 | ✅ `plan` | full, java-python, lite |
| C1 | ✅ `plan-prd` | full, java-python, lite |
| C1 | ✅ `prp-plan` | full, java-python, lite |
| C1 | ✅ `prp-prd` | full, java-python, lite |
| C2 | ✅ `prp-implement` | full, java-python, lite |
| C2 | ✅ `feature-dev` | full, java-python, lite |
| C2 | ✅ `build-fix` | full, java-python, lite |
| C3 | ✅ `code-review` | full, java-python, lite |
| C3 | ✅ `refactor-clean` | full, java-python, lite |
| C4 | ✅ `test-coverage` | full, java-python, lite |
| C4 | ✅ `fastapi-review` | full, java-python, lite |
| C5 | ✅ `pr` | full, java-python, lite |
| C5 | ✅ `prp-pr` | full, java-python, lite |
| C5 | ✅ `prp-commit` | full, java-python, lite |
| C6 | ✅ `update-docs` | full, java-python |
| C6 | ✅ `update-codemaps` | full, java-python |
| C7 | ✅ `cpp-test` | full, java-python |
| C7 | ✅ `flutter-test` | full, java-python |
| C7 | ✅ `go-test` | full, java-python |
| C7 | ✅ `gradle-build` | full, java-python |
| C7 | ✅ `kotlin-test` | full, java-python |
| C7 | ✅ `react-test` | full, java-python |
| C7 | ✅ `rust-test` | full, java-python |
| C8 | ✅ `aside` | full, java-python, lite |

## Agents

| 组 | 名称 | 生效 profile |
| --- | --- | --- |
| A1 | ✅ `code-reviewer` | full, java-python, lite |
| A1 | ✅ `commit-reviewer` | full, java-python, lite |
| A1 | ✅ `pr-test-analyzer` | full, java-python |
| A1 | ✅ `comment-analyzer` | full, java-python |
| A1 | ✅ `silent-failure-hunter` | full, java-python, lite |
| A1 | ✅ `type-design-analyzer` | full, java-python |
| A1 | ✅ `security-reviewer` | full, java-python, lite |
| A1 | ✅ `code-simplifier` | full, java-python, lite |
| A1 | ✅ `refactor-cleaner` | full, java-python, lite |
| A2 | ✅ `architect` | full, java-python |
| A2 | ✅ `code-architect` | full, java-python |
| A2 | ✅ `code-explorer` | full, java-python |
| A2 | ✅ `planner` | full, java-python |
| A2 | ✅ `build-error-resolver` | full, java-python |
| A2 | ✅ `performance-optimizer` | full, java-python |
| A2 | ✅ `tdd-guide` | full, java-python |
| A2 | ✅ `e2e-runner` | full, java-python |
| A2 | ✅ `spec-miner` | full, java-python |
| A3 | ✅ `java-reviewer` | full, java-python, lite |
| A3 | ✅ `java-build-resolver` | full, java-python, lite |
| A3 | ✅ `kotlin-reviewer` | full, java-python, lite |
| A3 | ✅ `kotlin-build-resolver` | full, java-python, lite |
| A4 | ✅ `python-reviewer` | full, java-python, lite |
| A4 | ✅ `django-reviewer` | full, java-python, lite |
| A4 | ✅ `django-build-resolver` | full, java-python, lite |
| A4 | ✅ `fastapi-reviewer` | full, java-python, lite |
| A5 | ⬜ `typescript-reviewer` | full |
| A5 | ⬜ `react-reviewer` | full |
| A5 | ⬜ `react-build-resolver` | full |
| A5 | ⬜ `vue-reviewer` | full |
| A6 | ⬜ `go-reviewer` | full |
| A6 | ⬜ `go-build-resolver` | full |
| A6 | ⬜ `rust-reviewer` | full |
| A6 | ⬜ `rust-build-resolver` | full |
| A6 | ⬜ `cpp-reviewer` | full |
| A6 | ⬜ `cpp-build-resolver` | full |
| A6 | ⬜ `csharp-reviewer` | full |
| A6 | ⬜ `php-reviewer` | full |
| A6 | ⬜ `ruby-reviewer` | full |
| A6 | ⬜ `swift-reviewer` | full |
| A6 | ⬜ `swift-build-resolver` | full |
| A6 | ⬜ `dart-build-resolver` | full |
| A6 | ⬜ `flutter-reviewer` | full |
| A6 | ⬜ `fsharp-reviewer` | full |
| A6 | ⬜ `harmonyos-app-resolver` | full |
| A6 | ⬜ `pytorch-build-resolver` | full |
| A7 | ✅ `database-reviewer` | full, java-python |
| A7 | ✅ `network-architect` | full, java-python |
| A7 | ✅ `network-config-reviewer` | full, java-python |
| A7 | ✅ `network-troubleshooter` | full, java-python |
| A7 | ✅ `homelab-architect` | full, java-python |
| A7 | ⬜ `rag-pipeline-reviewer` | full |
| A7 | ⬜ `mle-reviewer` | full |
| A8 | ⬜ `doc-updater` | full |
| A8 | ⬜ `docs-lookup` | full |
| A8 | ⬜ `opensource-forker` | full |
| A8 | ⬜ `opensource-packager` | full |
| A8 | ⬜ `opensource-sanitizer` | full |
| A9 | ⬜ `a11y-architect` | — |
| A9 | ⬜ `bengali-reviewer` | — |
| A9 | ⬜ `healthcare-reviewer` | — |
| A9 | ⬜ `chief-of-staff` | — |
| A9 | ⬜ `marketing-agent` | — |
| A9 | ⬜ `seo-specialist` | — |
| A9 | ⬜ `conversation-analyzer` | — |
| A9 | ⬜ `agent-evaluator` | — |
| A9 | ⬜ `harness-optimizer` | — |
| A9 | ⬜ `loop-operator` | — |
| A10 | ⬜ `gan-planner` | — |
| A10 | ⬜ `gan-generator` | — |
| A10 | ⬜ `gan-evaluator` | — |

## fork 自有资产

- skill：`ecc-omp-router`（选路表：任务 → skill / agent / command 组合）
- rules：`omp-tooling` `omp-delegation` `fork-workflow` `fork-verification` `fork-coding-style`
