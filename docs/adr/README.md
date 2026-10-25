# 决定记录（ADR）

本目录记录本 fork 的架构决定。

| ADR | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-upstream-adaptation-in-materialization.md) | 上游文本的改写只发生在物化层 | accepted | 2026-10-24 |
| [0002](0002-single-reference-judgment.md) | 引用判定只有一份实现 | accepted | 2026-10-24 |
| [0003](0003-fork-catalog-references-are-notices.md) | fork 自有目录里的裁剪引用只记 notice | accepted | 2026-10-24 |
| [0004](0004-upstream-pin-single-source-of-truth.md) | 上游 pin 是唯一事实源，同步只开 PR | accepted | 2026-10-24 |
| [0005](0005-adaptation-invariant-gate.md) | omp 适配由不变式门禁守住 | accepted | 2026-10-24 |
| [0006](0006-plugin-state-and-attribution.md) | 插件状态与归属判定 | accepted | 2026-10-24 |
| [0007](0007-runtime-name-prefix.md) | 运行名带 `ecc-omp-` 前缀，只用于区分 | accepted | 2026-10-25 |

这些 ADR 是 fork 自有的仓库文档，不参与物化，也不随 profile 裁剪。
