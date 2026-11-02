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
| [0008](0008-no-commands-and-deduplicate-against-installed-plugins.md) | 不发布命令，与其它插件重复的 skill 与 agent 一律不物化 | accepted | 2026-10-28 |
| [0009](0009-ship-ops-skills-and-mattpocock-boundary.md) | 以 mattpocock 为重叠基准，ECC fork 补齐发布 / 部署 / 运维能力 | accepted | 2026-11-01 |
| [0010](0010-absorbed-pool-for-third-party-skills.md) | 第三方 skill 以「收纳池」形式纳入，与上游池分离 | accepted | 2026-11-01 |
| [0011](0011-chinese-skill-descriptions.md) | skill 的提示行描述改成中文，靠一张触发描述表维护 | accepted | 2026-11-02 |

这些 ADR 是 fork 自有的仓库文档，不参与物化，也不随 profile 裁剪。
