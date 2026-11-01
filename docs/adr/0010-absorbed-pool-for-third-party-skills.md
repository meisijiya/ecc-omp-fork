# ADR-0010: 第三方 skill 以「收纳池」形式纳入，与上游池分离

**Date**: 2026-11-01
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

本 fork 的能力缺口有两类：一类是上游 ECC 没有的（发布 / 运维 / 可观测，已由 ADR-0009 的自有 skill 补上），另一类是**上游与 mattpocock 都没有**的通用工程能力——把反复出现的错误变成结构性约束、把项目质量底线写成契约并盯住被悄悄降低的门槛、状态机的形式化验证、任务重写。

这些能力只存在于两个第三方仓：`backnotprop/pstack`（58 条 skill）与 `addyosmani/agent-skills`（25 条）。逐条筛过之后，真正「独立、且与本机已装的 mattpocock、ponytail、PUA、caveman、qa-skills 以及本 fork 现有资产都不重叠」的只剩 6 条运行条目（pstack 的 24 条 `principle-*` 里取 8 条无重叠的合成 1 条 bundle）。

放进本 fork 立刻撞上三条既有约束：

1. **`pool/` 不能碰。** 池摘要由 `tools/sync_upstream.py` 的 `compute_pool_digest()` 计算，`tools/check_upstream_pin.py` 校验「pin ↔ 内容」一致；往 `pool/` 塞第三方文件即门禁红（ADR-0004）。
2. **`own/` 没有上游追踪。** `own/skills` 是 fork 自有资产，永远包含、不记上游 sha（`tools/apply_selection.py`），放进去就失去了「按上游版本同步」的能力。
3. **profile 分流要能生效。** `own/skills` 无条件进所有 profile，而 `statechart`、`typescript-best-practices` 只该进 `full`。

另外，`GLOSSARY.md` 明确禁止把上游池写成 `vendor`，而 `manifest/external_refs.json` 已经占用了「外部」一词的含义（别的插件提供、本 fork 不提供）。

## Decision

1. **新建收纳池 `absorbed/<source>/`**，与上游池同构、互不干扰：`pool/` 仍是上游快照，`absorbed/` 是改写后的第三方副本，`own/` 是 fork 自撰。三者物化到同一棵运行树。
2. **每个来源 pin 到具体 commit**（`manifest/absorbed.json` 的 `sources.<slug>.commit`），手动 bump，不自动跟 HEAD——与上游 pin 同语义。
3. **改写由声明式规则完成**（`tools/absorbed_fixups.py`），`tools/sync_absorbed.py` 在拉取后重放规则并落盘；规则命中数不为 1 即失败，避免上游改写后静默半适配。规则覆盖：斜杠触发词（ADR-0008 下无命令可指，INV-14）、`.claude/` 与 `CLAUDE.md`（INV-02/03）、宿主专有 frontmatter 键（`disable-model-invocation`、`paths`）与兄弟 skill 链接；`Claude Code` 措辞与 Claude 工具名由 `check_adapt` 的 INV-05/INV-15 在物化期兜底，`check_absorbed` 另做离线残留扫描。
4. **运行名统一带 `ecc-omp-` 前缀**（ADR-0007 同一条规则）；来源可追溯性由 `manifest/absorbed.json` 承担，不靠名字编码。
5. **profile 按条分流**：`correct`、`sharpen`、`engineering-principles`、`constraint-driven-development` 进 `java-python` 与 `full`；`statechart`、`typescript-best-practices` 只进 `full`；`lite` 一条不进。条目名写在 `manifest/profiles/<p>.json` 的 `absorbed` 数组里。
6. **24 条 principle 中取 8 条合成一条** `ecc-omp-engineering-principles`（8 小节），由 `sync_absorbed.py` 从 `absorbed/pstack/principles/` 的 8 份原始快照拼接生成；手改生成物会被门禁抓住。
7. **新增门禁 `tools/check_absorbed.py`**（离线）：校验来源 pin 形状与 manifest 内部一致性、每个 skill 的文件摘要集合、生成物与其输入是否一致、各来源的许可文本与版权行、换行符（CRLF 会让干净 clone 的摘要对不上），以及改写后是否残留不变式禁止的文本。

## Alternatives

- **放 `pool/`**：污染池摘要，`check_upstream_pin` 直接红。
- **放 `own/skills/`**：无法按 profile 分流（`own/` 永远全进），且丢失上游 sha，无法判断「上游改了什么」。
- **git submodule**：溯源干净，但两仓的 `skills/` 布局不同，仍需一层物化；Windows 下 submodule 维护成本高于一个 pin 文件。
- **只放 magpie 用户级库、不进 fork**：本机 `~/.config/magpie/library/skills/` 已有 addyosmani 的 25 条同名目录，但它们在 `~/.config/magpie/library.json` 的 `applied.omp.skills` 里均未激活，且不受 fork 的适配不变式约束。

## Consequences

- 运行树新增 4 条（`java-python`）/ 6 条（`full`）skill，注入约 +0.38K / +0.50K tok（估算，name+description，CJK 1.05 tok/字、ASCII 1/3.5 字符）。
- `absorbed/` 体积约 320KB，其中 `statechart/scripts/` 占 202KB（排除了上游 3.3MB 的测试语料）。
- 上游改写会以「规则命中数 ≠ 1」的形式失败，必须人工确认后改规则——这是有意的：静默半适配会以损坏的 skill 形式进入提示。
- `absorbed/` 里的 skill 正文与 description 保留上游英文；只有生成的 bundle 的 description 由脚本写成中文。斜杠触发词、`CLAUDE.md` 等按改写表处理。
- 未收纳的候选见下节评估记录，结论是「与 ECC / mattpocock 重叠」或「依赖其体系」。
- 实现侧的隐式决定（ADR 正文未逐条展开）：目录镜像上游布局 `absorbed/<source>/skills/<name>/`；`principles/` 保留未改写的原始快照（供 bundle 重新生成，不参与物化）；写盘副本的 frontmatter 已内嵌运行名，因此摘要与 `ecc-omp-` 前缀绑定；收纳名并入 `refscan.pool_sets()`，使未物化的收纳资产被判为「裁剪」而非「未知」；NOTICE.md 不记收纳来源的 commit（该文件只允许出现一个 40 位 sha）；许可文本随 `absorbed/<source>/LICENSE` 走，并由门禁校验。

## 评估记录（未收纳）

| 来源 | 条目 | 未收纳原因 |
| --- | --- | --- |
| pstack | `arena` `swarm` `why` `architect` `figure-it-out` `show-me-your-work` `how` `teach` `poteto-mode` `poteto-help` `setup-pstack` `automate-me` `reflect` `recall` `ketchup-video` `make-bot-ui` `no-comments` `create-verification-skill` `maintain-verification-skill` `create-formal-verification-skill` `maintain-formal-verification-skill` | 依赖 pstack 体系：模型设置文件、`agents/`、`playbooks/`、harness transcript 目录、Pele 渲染器 |
| pstack | `tdd` `interrogate` `bro` `blast-radius` `benchmark-checklist` `unslop` `technical-writing` | 与 mattpocock `tdd` / `grilling` / `wait-what` 或 ECC `change-impact`、`benchmark`、`docs-governance` 重叠；`unslop` 另与本机 `lieflat-less-ai-tone` 重叠 |
| pstack | `laziness-protocol` `subtract-before-you-add` `guard-the-context-window` `boundary-discipline` `model-the-domain` `prove-it-works` `test-behavior-not-implementation` `encode-lessons-in-structure` `migrate-callers-then-delete-legacy-apis` `never-block-on-the-human` `explain-the-number` `attack-the-premise` `build-the-lever` `minimize-reader-load` `principle-fix-root-causes` `principle-type-system-discipline` | 与 ponytail、mattpocock `domain-modeling`、本 fork 规则或 `correct` 本身重叠（后两条分别被 `correct` 的「先修根因」与 `typescript-best-practices` 的正文吸收） |
| pstack | `in-your-own-words` `ketchup` | 价值低于占行成本：前者是 315B 的一句话提示，后者依赖 `bro` 的语感而 `bro` 与 mattpocock `wait-what` 重叠 |
| addyosmani | `api-and-interface-design` `code-review-and-quality` `code-simplification` `security-and-hardening` `observability-and-instrumentation` `performance-optimization` `ci-cd-and-automation` `shipping-and-launch` `git-workflow-and-versioning` `test-driven-development` `browser-testing-with-devtools` `deprecation-and-migration` `frontend-ui-engineering` `source-driven-development` `incremental-implementation` `documentation-and-adrs` `planning-and-task-breakdown` `debugging-and-error-recovery` `spec-driven-development` `doubt-driven-development` `idea-refine` `using-agent-skills` `context-engineering` | 与本 fork 现有 skill / agent 或 mattpocock 同名功能重叠 |
| addyosmani | `interview-me` | 触发词与 mattpocock `grilling` 正面冲突（其自身列了 "grill me" / "stress-test my thinking"），按 ADR-0009「一事一入口」不引入 |

算术闭合：pstack 58 = 4 条收纳 skill + 8 条 principle 输入（合成 bundle）+ 46 条未收纳
（34 条普通 skill − 4 条收纳 = 30，加 16 条未用 principle）；addyosmani 25 = 1 条收纳 + 24 条未收纳。
合计收纳 6 条运行条目（含 1 条生成物）。
