# 变更记录

本文件记录本插件的对外变更，格式按 Keep-a-Changelog，版本号遵循 SemVer。
版本号记在 `package.json` 的 `version`，发布 tag 一律用 `v<semver>`。

## [0.5.0] - 2026-11-03

### Breaking

- **运行名与安装根改名**：skill / agent 运行名从 `ecc-omp-*` 改为 `forge-*`，插件 id 与安装根
  从 `ecc-omp-fork` 改为 `omp-skill-forge`（`~/.omp/agent/local/omp-skill-forge`）。
  旧名的资产不再存在，旧安装需要 `omp plugin uninstall ecc-omp-fork` 后重装。
  详见 [ADR-0013](docs/adr/0013-repository-renamed-to-omp-skill-forge.md)。
- **GitHub 仓库改名**：`meisijiya/ecc-omp-fork` → `meisijiya/omp-skill-forge`（旧地址会自动跳转）。
- **TypeScript 入口去重**：收纳池里的 `forge-typescript-best-practices` 不再物化，
  TypeScript 写法改由上游的 `forge-typescript-patterns` 承担。

### Added

- **qa-skills 全套收纳**：13 条 QA skill（含共享知识库 `forge-core`）进收纳池，
  进 `full` 与 `java-python` profile。覆盖需求分析、测试策略、用例写作与评审、探索式测试、
  端到端与接口测试执行、Bug 根因、回归范围、flaky 治理、跨会话质量知识库。
  详见 [ADR-0014](docs/adr/0014-qa-skills-absorption.md)。
- **逐资产上游版本台账**：`tools/upstream_versions.py` 与 `manifest/asset_versions.json`，
  按 git tree oid 记 4 个来源 224 个资产的内容指纹（ECC 205 / pstack 5 / qa-skills 13 /
  addyosmani 1），`check` 报漂移、`check --offline`
  校验覆盖并接入 CI。详见 [ADR-0015](docs/adr/0015-per-asset-upstream-version-ledger.md)。
- **插件自己的运维 skill**：`forge-pipeline`（更新与发布流水线）、`forge-ci-triage`
  （CI 失败定位）、`forge-absorb-third-party-skill`（收纳第三方 skill），随插件分发。
- **收纳池的整源批量改写规则**：`absorbed_fixups.py` 新增 `SOURCE_RULES`，每条带期望命中
  总数，上游改了写法而规则没跟上时同步直接失败。

### Changed

- **上游 pin 前进**：`90606c8` → `b38be6a`，pool 随之刷新（134 skills / 24 commands /
  71 agents），新增上游 skill `typescript-patterns` 与 `module-governance` 已分类进 group。
- **提示行规模**（默认 profile `java-python`）：73 → 89 个 skill；`full` 137 → 154；
  `lite` 43 → 46。描述 token 约 2.8K，名称 token 约 0.5K。
- **中文触发描述**扩到 153 条 skill 与 71 条 agent。

### Fixed

- **收纳 skill 的内容不再被静默丢弃**：`refscan.source_exists()` 补上 `absorbed/` 探测，
  物化期出现 drop 动作直接失败。修复了 `forge-constraint-driven-development` 丢失
  「Loading Constraints」整节与阶段表命令列、`forge-typescript-best-practices` 误判工具名
  等问题。
- **上游示例里的宿主命令行改写**：`claude -p --allowedTools --dangerously-skip-permissions`
  改成 omp 的 `omp -p --tools= --auto-approve`。

## [0.4.0] - 2026-11-02

- agent 的提示行描述全量改成中文，与 skill 侧复用同一张描述表机制。

## [0.3.0] - 2026-11-01

- 新增发布 / 可观测性 / 事故响应三条运维 skill；引入收纳资产池（6 条第三方补缺 skill）。
