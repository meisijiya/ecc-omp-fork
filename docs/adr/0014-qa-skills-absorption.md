# ADR-0014: 以收纳池纳入 fishzjp/qa-skills 的 QA 套件，并划清与 ECC e2e-testing 的分工

**Date**: 2026-11-03
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

本 fork 的测试侧能力主要来自 ECC（`test-collaboration`、`e2e-testing`、`tdd`、
`verification-loop` 等），没有「怎么设计一颗测试用例、怎么定测试策略、怎么判 Bug
根因、怎么管 flaky」这一整条链路。`fishzjp/qa-skills`（MIT，13 个目录、39 个文件、
392K）正好是这条链路：`qa` 编排阶段，`requirement-analysis` / `test-strategy` /
`test-case-writing` / `test-case-review` / `exploratory-testing` /
`automated-e2e-testing` / `api-testing` / `bug-analysis` / `regression-testing` /
`test-reliability` / `qa-memory` 各管一段，共用一个不面向触发的知识库 `core`。

它不能直接拷进来：

1. `core` 被其余 12 条以相对路径 `../core/<file>` 引用 146 处（反引号裸路径，无
   markdown 链接），另有 5 处以 `python3 ../core/scripts/*.py` 形式执行。这些路径在
   本 fork 的物化布局（`skills/forge-<name>/`）下一律失效。
2. 三条宿主残留：`qa-memory` 两处 `CLAUDE.md` 提法，`core/pipeline-integration.md`
   一处 `claude -p --allowedTools --dangerously-skip-permissions` 的 CI 示例。
3. frontmatter 里有 `slug` / `displayName` 两个 marketplace 专用键，omp 不读。
4. `automated-e2e-testing` 与 ECC 的 `e2e-testing` 语义相邻。

## Decision

1. **整套收纳，`core` 也收**。`core` 是依赖单元不是工作流，但少了它其余 12 条全是
   断链；上游的 `core/SKILL.md` 自己就用 `When NOT to Use` 声明「不独立触发」。运行名
   `forge-core`（manifest 键必须等于上游目录末段，`check_absorbed.py` 断言这一点），
   中文描述写明它是共享知识库，靠描述而非拦截降触发率。
2. **`core` 的共享 .md 留在技能目录顶层**，不搬进 `references/`：omp 只把
   `skills/*/SKILL.md` 当技能发现（`omp skill list` 实测不含上游同布局的
   `security-review/cloud-infrastructure-security.md`），顶层散文件不会污染提示；搬移
   只会让 146 处引用对不上上游。
3. **引用改写走声明式规则**，不手工改收纳副本：
   - 整源批量规则落在 `tools/absorbed_fixups.py` 的新 `SOURCE_RULES`，每条带期望命中
     总数（`python3 ../core/scripts/` 5 处、`../core/` 141 处、`` `qa` `` 19 处、
     `` `core` `` 1 处、`slug` / `displayName` 各 13 处）。总数不符即 `Drift`，
     `tools/sync_absorbed.py` 直接失败——上游改了写法而规则没跟上是阻断，不是静默。
   - 读文件的地方改写成 `skill://forge-core/<file>`（本 fork 既有的可跟随形式）；要执行
     脚本的地方改写成 `python3 <forge-core-skill>/scripts/<x>.py`，与 ECC 自己的
     `<docs-governance-skill>/scripts/audit-docs.py` 占位写法同一口径，
     `own/rules/omp-tooling.md` 说明占位如何落到插件内的真实目录。
   - 逐文件规则处理路径口径注记、`core` 目录说明、`CLAUDE.md` 两处与 CI 示例
     （`claude -p` → `omp -p`、`--allowedTools` → `--tools=`、
     `--dangerously-skip-permissions` → `--auto-approve`）。
4. **profile 分流**：整套进 `full` 与 `java-python`，`lite` 一条不收（lite 是每轮提示
   开销最低的档，13 条 QA 加约 0.6K token）。`lite` 下少数上游 skill 正文里指向 QA
   skill 的反引号裸名会按现有规则降级为 notice，不构成悬空。
5. **与 ECC `e2e-testing` 的分工**：两条都留，因为入口不同——ECC 的是 Playwright 工程
   模式（POM、配置、CI、产物、Web3 场景），qa 的是流水线里的执行阶段（把
   `execution_model: ui` 的用例变成可跑代码并回填证据与报告）。中文描述各写各的触发
   词，`forge-router` 的选路表把「写 Playwright 测试」与「跑完端到端测试全流程」分到
   不同行。不合并的代价是两条相邻能力并存，收益是两边都不用削减内容。
6. **许可**：MIT，版权行进 `manifest/absorbed.json`，正文沿 `absorbed/qa-skills/LICENSE`
   走，`NOTICE.md` 补第三段许可全文并列出 19 条收纳条目。

## Alternatives

- **只收高价值的 4 条**（`qa`、`test-strategy`、`test-case-writing`、`core`）：能跑通，
  但其余 9 条的交叉引用会大面积悬空，且丢掉 Bug 分析与 flaky 治理这两块本 fork 真缺的
  能力。
- **把 13 条压成 1 条大 skill**：省 13 次提示行开销，但丢掉「按阶段按需加载」的设计，
  每次都要读 300K 正文，得不偿失。
- **保留 `core` 的 `../core/` 相对写法并扩展 refscan 认它**：会让本 fork 出现第二套路径
  约定，与 `skill://` 单一约定冲突。

## Consequences

- 收纳池从 6 条涨到 19 条，`java-python` 生效 skills 从 73 涨到 86，提示行描述开销
  从约 2.5K 涨到约 2.7K token（新增 17 条约 560 token）。
- `tools/absorbed_fixups.py` 新增 `SOURCE_RULES` + 命中总数校验 + `verify_source_counts()`；
  改上游、改前缀（规则里用的 `{prefix}`）都只需改规则或常量再重跑 `sync_absorbed.py`。
- 上游若把 `core/` 改名或拆包，`verify_source_counts()` 会以命中数不符失败，维护者据此
  重写规则，而不是让断链静默进运行树。
- `forge-core` 出现在技能列表里但正文声明「不独立触发」；若模型误触发，产出的只是一份
  方法清单，不改变被测项目。
