# ADR-0001: 上游文本的改写只发生在物化层

**Date**: 2026-10-24
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

上游资产池里的文本带着 Claude Code 这类 harness 假设：CLAUDE.md 路径、.claude/ 目录、Claude 专有工具名、agent frontmatter 里的 model: sonnet 行。omp 不认这些假设，运行树必须不含它们，否则资产在 omp 里不可用。改写可以落在上游资产池、物化层、运行树三处，但三处的归属与可审计性差别很大。

## Decision

上游文本的改写只发生在物化层：`tools/apply_selection.py` 里的规则表，加上 `own/patches/` 里的整份替换件。上游资产池保持原样，运行树是生成物，不许手改。

## Alternatives Considered

### Alternative 1: 直接改上游资产池

- **Pros**: 改动一眼可见，最省工具。
- **Cons**: 每次同步上游都会被覆盖；「裁剪 + omp 适配」与「上游更新」混在一起，无法审计也无法回放。
- **Why not**: 上游资产池是外部输入，改它等于让本 fork 改写上游，下次同步必然冲突。

### Alternative 2: 手改运行树

- **Pros**: 不需要任何工具，改完立刻可见。
- **Cons**: 每次物化即丢失，也无法保证幂等。
- **Why not**: 运行树是生成物，手改等于把生成结果当成真相来源。

## Consequences

### Positive

- 同步上游与适配改动互不干扰，两者可以分别审。
- 物化可重放：同一份选集每次得到同样的运行树，差异可比。

### Negative

- 多一层工具：要改上游措辞，得先改规则表或整份替换件。
- 规则表与 `own/patches/` 两处都要维护，omp 适配不变式的落点变多。

### Risks

- 规则覆盖不到上游新出现的措辞，运行树里可能漏掉 harness 假设；由 omp 适配门禁兜底。
