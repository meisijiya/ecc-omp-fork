# ADR-0005: omp 适配由不变式门禁守住

**Date**: 2026-10-24
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

omp 适配是规则驱动的文本改写，把上游资产池里的 harness 措辞改写成 omp 措辞。上游资产池随时会引入新措辞，纯靠人工评审必然漏检，而漏检一旦进入物化结果就会污染运行树。需要一条可判定的边界：哪些「Claude」字样允许保留（指向 Anthropic 产品或生态的），哪些必须改掉（把 Claude Code 当 harness 用的）。

## Decision

用一条门禁守住 omp 适配，形式是一组适配不变式：禁止 agent frontmatter 里的模型别名行，禁止 CLAUDE.md 路径，禁止 .claude/ 目录，禁止调用 Claude 命令行，禁止 Claude 工具名，禁止「Claude Code」措辞，斜杠命令引用不得越出物化出来的命令名单，各类资产的 frontmatter 必须完整。

指向 Anthropic 产品或生态的写法允许保留，包括 Claude API、Claude Desktop、claude-haiku 模型名、ECC 命令行的 claude-project 参数，以及 docs-governance 的 CLAUDE_MAP.md 文档角色名；C# 与 Swift 的 Task 是类型名，不算 Claude 工具名；门禁只对一条自有 rule 做硬编码豁免。

## Alternatives Considered

### Alternative 1: 全仓禁止出现「Claude」

- **Pros**: 判定最简单，一条字面规则就能覆盖全部情况。
- **Cons**: 会误伤 Anthropic 产品名与 C#/Swift 类型名。
- **Why not**: 不变式要守的是 harness 措辞，不是字面量本身。

### Alternative 2: 只靠人工评审

- **Pros**: 判定带上下文，可以处理门禁没覆盖到的写法。
- **Cons**: 漏检，且上游每次同步都要重看一遍。
- **Why not**: 上游资产池的变动频率让人工复核不可持续。

## Consequences

### Positive
- omp 适配不靠人眼，例外集中在一处可审计。
- 上游引入新措辞时，遗漏由门禁暴露，而不是等到运行树出问题。

### Negative
- 新增例外要改工具，不能只在文本里加注绕过。
- 门禁覆盖四类资产，越界与误判都要逐条修正。

### Risks
- 不变式可能过严或过松，靠负向测试样本持续校正。
