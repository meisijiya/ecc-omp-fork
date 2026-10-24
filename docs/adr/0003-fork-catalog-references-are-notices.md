# ADR-0003: fork 自有目录里的裁剪引用只记 notice

**Date**: 2026-10-24
**Status**: accepted
**Deciders**: 本 fork 维护者

## Context

物化时会删掉当前 profile 没有的资产引用，所以运行树里剩下的裁剪引用只可能出现在 fork 自有资产的文件（自有 skill 与自有 rule，及其运行树副本）——这些文件描述的是整个 fork 的目录，本来就会点名别的 profile 的资产。同时 `skill://` 这类写法是可执行指针，指向当前 profile 不可解析的名字就是悬空引用。两类情况的严重程度并不相同。

## Decision

裸反引号形式的描述性引用出现在 fork 自有资产里且被 profile 裁掉，记 notice，不算缺陷；`skill://` 等可执行指针形式在任何文件里指向不可解析的名字，是缺陷；`own/patches/` 不适用 fork 自有豁免，它整份替换上游资产，原样进运行树。判定归属的 fork 自有文件清单由 `tools/refscan.py` 提供，缺陷与 notice 的分类由 `tools/check_refs.py` 负责。

## Alternatives Considered

### Alternative 1: 一律算缺陷

- **Pros**: 判定只有一个标准，不需要维护豁免清单。
- **Cons**: lite profile 永远红，门禁无法用于 CI。
- **Why not**: 门禁若在每个 profile 上都失败，就没有可用的自动化信号。

### Alternative 2: 一律算 notice

- **Pros**: 门禁在所有 profile 上都能通过。
- **Cons**: 真悬空会漏检。
- **Why not**: 可执行指针指向不存在的名字，模型照样会去读不存在的路径，必须保留为缺陷。

## Consequences

### Positive

- CI 可以在三个 profile 上都绿，裁剪与悬空有清晰分界。
- 缺陷与 notice 分开列出，排查时能直接区分「上游裁剪造成」和「真的写错了」。

### Negative

- 同一类问题在不同文件里判定不同，需要文档解释。
- 门禁输出不再只有单一结论，读结果的人要先看分类。

### Risks

- 豁免清单要随 fork 自有资产的变化维护；新增自有文件若未进入清单，其中的裁剪引用会被当成缺陷。
