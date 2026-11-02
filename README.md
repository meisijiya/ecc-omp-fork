# omp-skill-forge

> ECC（[affaan-m/ECC](https://github.com/affaan-m/ECC)）的 **omp 编程子集 fork**。
> 把 ECC 里跟编程相关的能力抽出来，做成可版本化、可增量更新的独立 omp 插件，
> 同时把每轮系统提示的 token 开销压到可控范围。

本仓库是**唯一事实源**。运行态安装根（`~/.omp/agent/local/omp-skill-forge`）由
`tools/deploy.py` 从这里同步过去，omp 通过 `omp plugin link` 指向该安装根。

默认 profile（`java-python`）下的生效规模：**86 skills + 22 agents + 5 rules**
（86 = 上游选中的 65 个 + 收纳资产池的 17 个 + 本 fork 自带的 4 个：`forge-router` 与发布 /
可观测性 / 事故响应三条运维 skill）；本 fork **不发布命令**，
换 profile 后的规模见「切换 profile」一节的表。

物化出来的 skill / agent 名统一带 `forge-` 前缀（上游名不带），例如
`skill://forge-api-design`、agent `forge-java-reviewer`。
前缀只用于**区分**：别的插件提供的同名资产仍用它自己的名字，本 fork 在
`manifest/external_refs.json` 里声明这些名字。

---

## 在 omp 中安装与配置

### 一条命令装好

```bash
git clone git@github.com:meisijiya/omp-skill-forge.git   # 私有库，走 SSH
cd omp-skill-forge
python tools/apply_selection.py     # 按当前 profile 物化 skills/agents/rules
python tools/build_catalog.py        # 刷新 docs/CATALOG.md（可选，但建议跟上游一起提交）
python tools/deploy.py              # 同步到 omp 安装根并 link
```

仓库是私有的，克隆需要你对 `meisijiya/omp-skill-forge` 的 SSH 读权限；匿名 https 克隆会 404。

`deploy.py` 做四件事：

1. 校验 `manifest/applied.json` 里的 profile 与 `manifest/selection.json` 的
   `active_profile` 是否一致（不一致直接退出，提示先跑 `apply_selection.py`）；
2. 把 `skills/ agents/ rules/` 同步到 `~/.omp/agent/local/omp-skill-forge`，
   并额外拷贝 `package.json` / `LICENSE` / `NOTICE.md`；
3. 执行 `omp plugin link ~/.omp/agent/local/omp-skill-forge`（重复 link 是安全的，不会报错），
   再跑一次 `omp plugin list`；
4. 用 `omp skill list` 校验物化出来的 skill 是否都被 omp 认到，对不上会打印清单并以
   退出码 1 结束（`--skip-verify` 可跳过这一步校验）。

顺带还会清掉早期布局留下的旧插件（`ecc-pi-core` / `ecc-programming`）：残留的 junction
会让同一批 skill 被注入系统提示两次，所以 `deploy.py` 每次都会顺手 uninstall + 删目录。

`omp plugin link` 在 Windows 上建的是**目录 junction**，目标是
`~/.omp/plugins/node_modules/omp-skill-forge`，它指向安装根
`~/.omp/agent/local/omp-skill-forge`（安装根里必须有 `package.json`，插件名取自其中的
`name: omp-skill-forge`）。链接关系可以直接查：

```bash
ls -l ~/.omp/plugins/node_modules/omp-skill-forge     # 应显示指向 .omp/agent/local 的链接
omp plugin list                                     # 应能看到 omp-skill-forge@0.4.0
```

装完后在 omp 里：

- 技能：`read skill://<name>`，例如 `read skill://forge-router`
- 规则：`read rule://<name>`，例如 `read rule://fork-workflow`
- 子代理：`task` 的 `agent` 字段填**裸名**，例如 `forge-java-reviewer`、`forge-python-reviewer`

改完资产后在 omp 会话里跑 `/reload-plugins`（技能即时刷新），
**agent 需要重开会话**才被发现。

### 手工安装（不想用脚本）

```bash
git clone git@github.com:meisijiya/omp-skill-forge.git   # 私有库，走 SSH
cd omp-skill-forge
python tools/apply_selection.py
# 把 skills/ agents/ rules/ package.json LICENSE NOTICE.md 复制到任意目录，例如：
mkdir -p ~/.omp/agent/local/omp-skill-forge
cp -r skills agents rules package.json LICENSE NOTICE.md ~/.omp/agent/local/omp-skill-forge/
omp plugin link ~/.omp/agent/local/omp-skill-forge
```

`LICENSE` 与 `NOTICE.md` 要一起复制：隔离门禁比对安装根与仓库树的 sha256，缺了会报 drift。

`omp plugin link <目录>` 直接把该目录挂进 `~/.omp/plugins/node_modules/<package name>`，
Windows 下是 junction。装完同样要 `/reload-plugins` 才在会话里生效。

### 启用与禁用（语义与自证）

本插件贡献的资产分三类：**skill / rule / agent**。它们同属一个插件根目录，
所以启停是**整体生效**的——不是「只关 skill、其余照旧」：

```bash
omp plugin disable omp-skill-forge    # 三类资产一起从 omp 的发现结果里消失
omp plugin enable  omp-skill-forge    # 恢复
```

- CLI 改完之后要 `/reload-plugins` 才会刷新当前会话的 skills / task agents / MCP；
  在 omp 的 TUI 里用 `/plugins enable|disable` 则会立刻刷新当前会话。
- 禁用只影响**本插件**提供的资产。若某个名字同时由别的来源提供（别的插件，或 omp
  自带的同名内置资产，例如 `security-reviewer`），禁用本插件后该名字仍会解析到别人的
  那份 —— 那是同名冲突，不是本插件残留。

自证脚本会自己跑一遍「禁用 → 探测 → 启用 → 探测」，并在 `finally` 里把插件恢复到
**执行前的原状态**（原来禁用就还禁用）：

```bash
python tools/check_plugin_isolation.py --toggle-test
```

- `--toggle-test`：临时禁用/启用本插件，验证三类资产在两种状态下的可见性是否符合预期。
- `--probe`：只观察当前状态，不改变任何东西（默认模式就是它）。
- `--omp <path>`：指定 omp 可执行文件（默认依次找 `OMP_BIN` 环境变量、`PATH` 上的 `omp`、
  Windows 启动器目录）；
  `--cwd` 覆盖运行 omp 的工作目录；`--root` 覆盖「定义本 fork 资产的那棵树」（默认取 omp
  实际链接的安装根，取不到才回落到仓库树）；`--json` 输出机器可读结果。

「本 fork 提供的资产」按**描述内容**判定，不按名字判定 —— 所以与 omp 内置 skill 同名不会误报。
工具还会逐文件比对「安装根 vs 仓库树」，两者不一致时直接判失败并提示跑
`python tools/deploy.py`。

退出码：

| 退出码 | 含义 |
| --- | --- |
| 0 | 与预期一致（禁用时四类都不再被提供，启用时全部可被提供） |
| 1 | 不一致：打印 FAIL 明细（禁用后仍有资产泄漏、启用后有资产缺失，或安装根与仓库树不一致） |
| 2 | 工具自身错误（例如找不到 omp 可执行文件、参数用法错误） |

归属看的是**运行时解析出来的描述**，不是系统提示里那一行：omp 会把过长的 skill 描述压短
再写进提示行，压缩结果缓存在 `~/.omp/agent/skill-descriptions.db`（表 `skill_descriptions`）。
所以本仓的 skill 描述大多在提示行里显示成压缩后的短句（`omp skill list` 里仍是
完整描述）——它们照样属于本插件。注意缓存里有行**不等于**该 skill 现在被启用（表里留着历史
残留）；启用性只由上面的差值与 `omp skill list` 证明。判定规则：

| 观察 | 含义 |
| --- | --- |
| 名字被提示，且 `omp skill list` 里是本仓的描述 | 本插件的资产（提示行可能是压缩过的短句） |
| 名字被提示，但 `omp skill list` 里不是本仓的描述 | 同名冲突：这个名字归别人 |
| 名字不被提示 | 本插件没有提供它 |

加 `forge-` 前缀之后，本 fork 的资产与 omp 内建资产不再重名：本仓的 agent 叫
`forge-java-reviewer`，omp 内建的是 `reviewer` / `scout` / `security-reviewer` 这类名字，
互不遮蔽。skill 侧本来就没有重名，加前缀后同样不重。

判定「本插件有没有泄漏」靠的是差值而不是名字表：同一轮探测里，提示行里的 skill 条目数在
启用态与禁用态之间的**差值恰好等于本仓的 skill 总数（86）**，少掉的正是这 86 个名字；
`omp skill list` 同时从 ours=86 变成 ours=0。提示行的总条目数会随别的插件增减而浮动，
所以只认差值，不认某个绝对值。rules 5、agents 22 是逐条按描述比对过的。

禁用只决定「本插件提供哪些资产」，不决定「文件还在不在磁盘上」：`omp plugin disable` 只是把
lockfile 里的 `enabled` 置成 false，插件目录（junction）仍然留在
`~/.omp/plugins/node_modules/` 下面。实测禁用后 `omp read skill://forge-api-design` 照样能读到这个
文件 —— read 的 URI 解析按插件目录找路径，不看 `enabled` 标志；卸载之后同一个 URI 才会报
`File not found`。想要「连文件都够不着」，走卸载。

### 卸载

```bash
# 方式一：脚本（会先跑 omp plugin uninstall，再删安装根）
python tools/deploy.py --uninstall

# 方式二：手工
omp plugin uninstall omp-skill-forge
rm -rf ~/.omp/agent/local/omp-skill-forge
```

`omp plugin uninstall` 会移除 `~/.omp/plugins/node_modules/omp-skill-forge` 里的链接，
并清掉 lockfile 里的运行时状态。安装根 `~/.omp/agent/local/omp-skill-forge` 是本仓
`deploy.py` 生成的产物，`omp plugin uninstall` 不会碰它，需要自己删
（或用 `python tools/deploy.py --uninstall` 一步删掉：它先跑 `omp plugin uninstall`，
再 `rmtree` 安装根）。

注意：**link 型插件不会出现在 `~/.omp/plugins/installed_plugins.json`** —— 那个文件只记
marketplace 安装的插件。link 型插件的启停状态记在
`~/.omp/plugins/omp-plugins.lock.json` 的 `plugins` 段里（形如
`"plugins": {"omp-skill-forge": {"version":"0.4.0","enabledFeatures":null,"enabled":true}}`；
该字段由 omp 在重新 link / 加载插件时刷新，`deploy.py` 不写它）。

### 升级

```bash
git pull
python tools/apply_selection.py     # 上游文本变了就重新物化
python tools/build_catalog.py        # 刷新 docs/CATALOG.md
python tools/deploy.py               # 同步到安装根并重新 link
```

然后在 omp 会话里 `/reload-plugins`：**skills 即时生效，新增的 agent 需要开一个
新会话**才会被 task discovery 发现。

### 切换 profile（改变每轮 token 开销）

profile 定义在 `manifest/profiles/`，当前指针在 `manifest/selection.json` 的
`active_profile` 字段（可选值：`full` / `java-python` / `lite`）。

```bash
# 1) 改指针
#    manifest/selection.json: "active_profile": "lite"
# 2) 重新物化、刷新目录并部署
python tools/apply_selection.py
python tools/build_catalog.py
python tools/deploy.py
```

| profile | skills | agents | 适用 |
| --- | --- | --- | --- |
| `java-python` | 82 | 22 | 默认。Java/Kotlin + Python/Django/FastAPI + 通用工程规范 + 测试与发布/运维 |
| `lite` | 39 | 11 | 每轮提示开销最低，只做后端核心 |
| `full` | 146 | 49 | 上游 `pi/core` 全量 + 全部编程 agent，冷门技术栈时用 |

表中数字 = 该 profile 从上游 `pool/` 选中的资产 + 收纳资产池的条目（与 `docs/CATALOG.md` 同口径），
**不含**本 fork 自带资产。收纳条目按 profile 分别是 `full` 19 条、`java-python` 17 条、`lite` 0 条，
所以物化后实际生效的 skills 数 = 上表数字 + 4（自有 `forge-router` 与发布 / 可观测性 /
事故响应三条运维 skill）：`full` 150、`java-python` 86、`lite` 43。agents 与上表一致，
rules 恒为自有 5 条。本 fork 不发布命令。

各 profile 的收益对比（技能描述进系统提示的部分）：

| profile | 描述 token | 名称 token | 合计 token |
| --- | --- | --- | --- |
| `full` | 4,667 | 975 | ~5.6K |
| `java-python` | 2,690 | 527 | ~3.2K |
| `lite` | 1,374 | 272 | ~1.6K |

描述 token 按中文一个字一个 token、其余字符三分之一 token 估算，名称按运行名字符数除以
3.5 估算。描述改成中文之后，三个 profile 的提示行都省下 1.5K 到 4.2K token：
`java-python` 从约 5.2K 降到约 3.2K，`full` 从约 9.8K 降到约 5.6K，`lite` 从约 3.1K
降到约 1.6K。

前缀本身的开销 = 6 字符 × 被改名的资产数（上游 + 收纳，自有资产的名字本就带前缀）：
`full` 技能名 +876、`java-python` +492、`lite` +234；agent 名同样带前缀，`java-python` 下 agent 名 +132。

`full` 物化后实际进系统提示的是 150 个 skill（127 个上游 + 19 个收纳 + 自带的 4 个）。
收纳资产在其中占约 731 token（19 条中文描述 619 + 运行名 112）；`java-python`
下收纳 17 条占约 659 token（描述 560 + 运行名 99）。

切完 profile 若不想把指针改动留在工作区，用下面这条还原（物化/部署脚本都只读它，
但手工或脚本重写这个 JSON 文件容易改掉缩进或末尾换行，还原后 diff 才干净）：

```bash
git checkout manifest/selection.json
```

### 上游同步（本地与 CI）

本地同步：

```bash
# 抓上游 HEAD → 刷新 pool/ → 写 pin → 定点改写 groups.json 的 upstream.commit → 重放 selection
python tools/sync_upstream.py

# 只刷新 pool/ 与 pin，不重放选择
python tools/sync_upstream.py --pool-only

# 不联网，只用本地已有的克隆
python tools/sync_upstream.py --no-fetch

# 把上游钉到某个 commit（40 位 hex；配合 --no-fetch 用本地已有 commit）
python tools/sync_upstream.py --checkout <40位hex commit>
```

`--checkout` 指定的 commit 不可达时脚本直接非零退出，**不会静默回退到 HEAD**。

CI 侧有定时任务 `.github/workflows/sync-upstream.yml`：

- 定时：`schedule` cron `17 3 * * 1`（UTC 周一 03:17）—— 定时任务会先问上游要当前 HEAD，
  再同步过去，所以上游一动，本仓的 pin 就会跟着走；
- 手动：`workflow_dispatch` 可填目标 commit，留空则用 `manifest/upstream.json` 里记录的 commit；
- push 触发：推到默认分支且路径命中 `pool/**`、`tools/**`、`manifest/**` 时也会跑（用记录的 commit）。

CI 用 `GITHUB_TOKEN` + `peter-evans/create-pull-request` 自动开 PR（分支
`chore/sync-upstream-<sha>`），**不直接推 main**。PR 里会跑全套门禁，并对
`full` / `java-python` / `lite` 三个 profile 依次物化 + 校验。上游内容没有变化时同步不产生
差异，也就不会有 PR —— PR 只在确实有变化时出现。

**pin 的唯一事实源是 `manifest/upstream.json`**（字段 `repo` / `commit` / `version` /
`pool_digest`）。其中 `pool_digest` 是 `pool/` 全部文件内容与相对路径的 sha256 摘要
（64 位小写 hex），写入端与校验端共用 `tools/sync_upstream.py` 里的同一个函数
`compute_pool_digest`，不会两套算法。`manifest/groups.json` 顶层的 `upstream` 块
（`repo` / `version` / `commit` / `skill_source` / `command_source` / `agent_source`）
是**同步镜像**：由 `sync_upstream.py` 定点改写其中的 `commit`，不是独立事实源。

`tools/sync_upstream.py` 的上游源解析顺序：
`.upstream/` 本地克隆 → omp marketplace 缓存克隆（`~/.omp/plugins/cache/marketplaces/ecc`）
→ 新克隆到 `.upstream/`。Windows 上 git 走 HTTP/2 容易中途断流，脚本对 clone 与 fetch
两条路径都强制 `http.version=HTTP/1.1`。

### 逐资产的版本台账

`pin` 只说「上游哪个 commit」，说不了「我手上这条 skill 是不是那个 commit 的样子」：
上游 ECC 的 skill 没有 `version:` 字段，pool 全量 grep 命中 0 处，qa-skills 这类收纳来源
虽然有版本号，但版本号不随每次改动走。所以按内容寻址：`manifest/asset_versions.json`
记录每个资产的 git tree oid（目录内容哈希），外加能读到的上游 `version:`（没有就是 null）。

```bash
# 记录当前上游状态（拉取 → 算 tree oid 与 version → 写台账）
python tools/upstream_versions.py record

# 逐条核对：上游有变化就打印哪几条、新老 oid，退出码 1
python tools/upstream_versions.py check

# 离线形状校验：台账覆盖每个来源的每个资产，tree 是 40 位 hex 或 null；不联网
python tools/upstream_versions.py check --offline

# 打印台账（离线）
python tools/upstream_versions.py show
```

资产清单的唯一真源还是 `manifest/`：ECC 的资产路径来自 `manifest/groups.json` 的
`skills`（`pi/core/skills/<name>`）与 `agents`（`agents/<name>.md`），收纳来源的路径来自
`manifest/absorbed.json` 的 `skills[*].path`。`forge-engineering-principles` 是本地拼接
生成物、上游没有对应目录，台账里 `tree` 为 null，`check` 视为「无需比对」。

`check` 报漂移之后的动作不是「拉一下」：先看是哪几条变了，再走对应链路——ECC 侧的走
`sync_upstream.py`（刷 `pool/` 与 pin）再 `apply_selection.py`；收纳侧的走
`sync_absorbed.py`（重放 `absorbed_fixups.py` 的规则）。两条链路都只改源副本，运行树永远
由物化重放生成，所以「同步」天然经过 omp 适配，不存在裸拉上游文本直接进运行树的路径。
规则命中数或摘要不符时链路会失败而不是静默通过。

### 门禁清单

| 命令 | 查什么 | 退出码 | 什么时候跑 |
| --- | --- | --- | --- |
| `python tools/check_refs.py [--json]` | **引用自洽**：运行树与 `own/` 里是否还有指向「本 fork 不提供的资产」的悬空引用（`skill://`、`skills/<name>/`、`commands\|agents\|rules/<name>.md`、斜杠命令、反引号裸名） | 0 = 无缺陷悬空（fork 自有目录里的 profile 裁剪引用只列出、不算缺陷）；1 = 有缺陷悬空（打印明细）；2 = profile 指针读不出来（`active_profile` 缺失或未知） | 每次改完运行树或上游文本后；提交前必跑 |
| `python tools/check_adapt.py [--tree <dir>] [--json]` | **omp 适配不变式**：INV-01..INV-15（无 `model:`、无 `CLAUDE.md`、无 `.claude/`、无 Claude CLI 调用、无 Claude 工具名、skill/agent/rule/command 的 frontmatter 完整性、`/name` 引用必须落在物化 commands 名单内、无「Claude Code」措辞等） | 0 = 无违规；1 = 有违规（逐条给 `文件:行号` + token）；2 = 用法错误或树不可读 | 每次改完运行树后；提交前必跑 |
| `python tools/check_upstream_pin.py` | **上游 pin 一致性**：`manifest/upstream.json` 形状（`commit` 必须是 40 位小写 hex、`repo` 非空）、`manifest/groups.json` 的 upstream.commit 镜像与 pin 一致、`pool/` 摘要等于 pin 的 `pool_digest`、`NOTICE.md` 引用的上游 commit 等于 pin 的 commit | 0 = 四项全过；1 = 有校验项不符（逐条打印）；2 = `manifest/upstream.json` / `manifest/groups.json` 读不出来 | 每次同步上游之后；提交前必跑 |
| `python tools/check_zh_descriptions.py [--json]` | **中文触发描述**：每条 skill 与 agent 都有中文 description（覆盖 upstream 与收纳），长度、标点与禁用句式合规 | 0 = 齐全且合规；1 = 有缺失或不合规（逐条打印）；2 = 表读不出来 | 改 `manifest/skill_descriptions.zh.json` / `manifest/agent_descriptions.zh.json` 或增删 skill/agent 之后；提交前必跑 |
| `python tools/check_absorbed.py [--json]` | **收纳池一致性**：`manifest/absorbed.json` 形状（来源 repo + 40 位 commit）、`absorbed/` 每个 skill 的文件摘要集合与 manifest 一致、生成物 `forge-engineering-principles` 等于其输入重新拼接的结果、收纳 skill 副本里不残留 `CLAUDE.md` / `.claude/` / `disable-model-invocation` / `paths` / 斜杠触发词（`absorbed/<source>/principles/` 是 bundle 的原始快照，按设计不改写、不在扫描面内） | 0 = 一致；1 = 有缺陷（逐条打印）；2 = manifest 读不出来 | 改了 `absorbed/`、`manifest/absorbed.json` 或 `tools/absorbed_fixups.py` 之后；提交前必跑 |
| `python tools/upstream_versions.py check --offline` | **逐资产版本台账形状**：`manifest/asset_versions.json` 覆盖每个来源的每个资产、没有多余条目、`tree` 是 40 位 hex 或 null | 0 = 覆盖一致；1 = 有缺失或多余（逐条打印）；2 = 台账或清单读不出来 | 增删 skill/agent、改 profile 或改 `manifest/absorbed.json` 之后；提交前必跑（不联网，CI 也跑这一条） |
| `python tools/check_plugin_isolation.py [--probe\|--toggle-test] [--omp <path>] [--cwd <dir>] [--root <dir>] [--json]` | **插件启停可见性**：本插件四类资产在启用态是否被 omp 提供、禁用态是否全部消失 | 0 = 符合预期；1 = 不一致（打印 FAIL 明细）；2 = 工具错误 | 改了部署方式、插件启停状态或 omp 版本之后 |

补充说明：

- `check_refs.py` 与 `check_adapt.py` 都是**检测型**门禁，只读不改运行树。
- **profile 裁剪与悬空引用的分界**：上游正文在物化时会把当前 profile 没有的资产引用删掉，
  所以运行树里剩下的「裁剪引用」只可能出现在 fork 自有的目录文件（`own/skills/`、`own/rules/`
  及其物化副本）——那两份文件描述的是整个 fork 的目录，本来就会点名别的 profile 的资产。
  这类引用被单独列出（`check_refs.py` 的 `profile_cropped_in_fork_catalog`），
  但不算缺陷；名字在 `pool/` 与 `manifest/absorbed.json` 里都不存在的引用在任何文件里都仍然是缺陷。
  `check_adapt.py` 的 INV-14 用同一条分界。
- `check_adapt.py` 只扫运行树 `skills/ commands/ agents/ rules/`（含子目录里的脚本文件），
  不扫 `own/`、`pool/`、`.github/`；`rules/omp-tooling.md` 在 INV-05 / INV-15 上是硬编码豁免
  （它是专门讲 Claude ↔ omp 工具对照的规则）。
- `Claude API`、`Claude Desktop`、`claude-haiku`、ECC CLI 的 `claude-project` 参数、
  `docs-governance` 的 `CLAUDE_MAP.md` 这些**指向 Anthropic 产品/生态**的写法，任何不变式都不会命中；
  被拦的是「把 Claude Code 当 harness 用」的措辞。
- `check_plugin_isolation.py --toggle-test` 会临时禁用再启用本插件，并用 `finally` 恢复到
  执行前的原状态，但它需要能执行 `omp plugin enable|disable`，所以要在本机跑，不适合放进 CI。
- 隔离门禁的两条判据都带证据，不是「看起来为空」：
  每次探测都会记录该运行面**广告了多少条**（`advertised`）、**是否存在**（`block`），
  以及一条本 fork 之外的用户级**对照技能**是否还在列表里；对照技能消失、或启用态广告数
  少于本仓资产数，都判为「探针不可信」而不是「干净」。
  skill 还多一路 `omp skill list` 描述级比对：它回答的是「omp 在这个名字下服务的是不是
  本仓的文本」，禁用态要求本仓的 skill 一条都不再带着本仓的描述被服务。
- 引用判定只有一份实现：`tools/refscan.py`，物化器与 `check_refs.py` 共用它。
- **上游名残留按缺陷处理**：运行树里若还出现上游名（`api-design`）而运行名是
  `forge-api-design`，`check_refs.py` 报 `upstream spelling of a renamed …` 并以退出码 1
  结束 —— 运行树里按上游名读不到资产。别的插件提供的资产（`manifest/external_refs.json`
  声明的）用它们自己的名字，不受这条约束。

### 其他可选配置

```bash
# 只加载指定技能（omp 全局设置，会影响其它插件的技能）
# 模式按运行名匹配，运行名带 forge- 前缀
# ~/.omp/agent/config.yml
skills:
  includeSkills:
    - "forge-java-*"
    - "forge-python-*"
    - "forge-springboot-*"
```

```yaml
# 隐藏个别技能的描述（仍可用 skill:// 读取，只是不进系统提示列表）
# skills/forge-<name>/SKILL.md 的 frontmatter 加一行：
hide: true
```

---

## 目录结构

| 路径 | 作用 |
| --- | --- |
| `pool/skills/` | 上游 ECC `pi/core` 的 132 个 skill 快照（未裁剪） |
| `pool/commands/` | 上游 ECC `pi/core` 的 24 个 command 快照（本 fork 不发布，仅留档回溯） |
| `pool/agents/` | 上游 ECC `agents/` 的 71 个 agent 快照（原始，含 Claude 专有 `model:` 行） |
| `absorbed/<source>/` | 收纳资产池：fork 之外仓库的 skill，经 `tools/absorbed_fixups.py` 改写后入库；各来源 `LICENSE` 随目录走（ADR-0010） |
| `own/skills/` | fork 自有 skill（`forge-router` 选路表 + 发布 / 可观测性 / 事故响应三条运维 skill），始终物化 |
| `own/rules/` | fork 自有 rules（5 条 omp 适配规则），始终物化 |
| `manifest/groups.json` | 三类资产的分类目录（分组 → 成员）；顶层 `upstream` 块是上游 pin 的同步镜像 |
| `manifest/profiles/` | profile 定义（组 + 排除项） |
| `manifest/selection.json` | 当前 profile 指针 + 额外追加项 |
| `manifest/applied.json` | 上次物化实际生效的 profile 与数量（部署前用来校验是否过期） |
| `manifest/upstream.json` | 上游 pin 唯一事实源：`repo` / `commit` / `version` / `pool_digest` |
| `manifest/absorbed.json` | 收纳来源 pin（`repo` + `commit`）、逐文件 sha256、bundle 配方、各来源许可与版权行 |
| `manifest/skill_descriptions.zh.json` | 每条 skill 的中文触发描述（物化时写入运行树，`pool/` 保持原样） |
| `manifest/agent_descriptions.zh.json` | 每条 agent 的中文触发描述（物化时写入运行树，`pool/` 保持原样） |
| `manifest/external_refs.json` | 本 fork 不提供、但由别的 omp 插件提供的资产（如 `code-review` skill）；这些名字不带本 fork 前缀 |
| `skills/` `agents/` `rules/` | **物化后的实际生效内容**（入库，便于 diff 上游变更）；skill 目录名、agent 文件名带 `forge-` 前缀 |
| `tools/` | 更新、裁剪、部署、生成目录、各项门禁的脚本 |
| `.github/workflows/sync-upstream.yml` | 定时 / 手动上游同步，自动开 PR 并跑全套门禁 |
| `docs/CATALOG.md` | 人类可读的资产目录（生成物） |
| `GLOSSARY.md` | 本 fork 的统一术语表（术语 + 含义 + 不要写的同义词） |
| `docs/adr/` | 本 fork 的决定记录（ADR），索引见 `docs/adr/README.md` |

---

## 常用命令

```bash
# 抓取上游最新 ECC，刷新 pool，重放选择，打印变更摘要
python tools/sync_upstream.py

# 只刷新 pool（不重放选择）
python tools/sync_upstream.py --pool-only

# 按当前 profile 重新物化 skills/ agents/ rules/
python tools/apply_selection.py

# 引用门禁：检查是否还有指向「本 fork 不提供的资产」的引用
python tools/check_refs.py

# 适配门禁：检查 omp 适配不变式（INV-01..INV-15）
python tools/check_adapt.py

# 上游 pin 门禁：检查 pin / 镜像 / pool 摘要三者一致
python tools/check_upstream_pin.py

# 收纳池门禁：来源 pin / 逐文件摘要 / 生成物 / 许可 / 换行符 / 残留文本
python tools/check_absorbed.py

# 中文触发描述门禁：覆盖、长度与句式
python tools/check_zh_descriptions.py

# 刷新收纳池（拉取两个来源的 pin → 重放改写规则 → 刷摘要 → 重新生成 bundle）
python tools/sync_absorbed.py

# 插件隔离自证：临时禁用→探测→启用→探测（finally 恢复原状态）
python tools/check_plugin_isolation.py --toggle-test

# 只观察当前插件可见性，不改变状态
python tools/check_plugin_isolation.py --probe

# 部署到 omp 的安装根并 link
python tools/deploy.py

# 部署但跳过 omp skill list 校验
python tools/deploy.py --skip-verify

# 卸载：omp plugin uninstall + 删除安装根
python tools/deploy.py --uninstall

# 重新生成资产目录文档
python tools/build_catalog.py
```

### 上游正文会被改写

`pool/` 里的上游快照是原样，但物化到 `skills/` `agents/` 时会做**确定性改写**：

- Claude 专有工具名与机制 → omp 的对应写法（`AskUserQuestion` → `ask`、
  `TodoWrite` → `todo`、删掉 `PreToolUse` hook 段等）。
- 路径约定（`CLAUDE.md` → `AGENTS.md`、`.claude/prds/` → `docs/prds/`）。
- **资产名统一加前缀**：上游名在物化时改名为运行名（`api-design` →
  `forge-api-design`、`code-reviewer` → `forge-code-reviewer`），正文里对它们的引用一并改写
  （`skill://api-design` → `skill://forge-api-design`、
  反引号裸名 → 带前缀的运行名）。散文里不是资产引用的普通词（"plan a meeting" 之类）
  不动。
- **agents 走同一条改写通道**：agents 与 skills 一样做工具名与路径改写，
  只是 agents 侧的 `Task` 改名规则被剔除 —— C#/Swift 的 `Task` 是类型名，改了会坏掉。
- **悬空引用清除**：指向本 fork 不提供的资产（上游全量 ECC 才有的命令、被当前 profile
  排除的兄弟 skill、嵌套 `rules/react/*.md`、上游 `docs/`）的引用会被删掉；
  指向可读资产的相对 markdown 链接会被改写成 omp 能跟随的规范 URI
  （`[react-testing](../react-testing/SKILL.md)` → `skill://forge-react-testing`）。
- **带 kind 前缀的引用**也会被识别并改写：`` `skill: foo` `` → `skill://foo`，
  ``rules: `foo/bar` `` 这类写法在指向可读资产时同样改成规范 URI；指向本 fork
  未提供的资产的会被剪掉。
- **变空的小节标题会一并删除**：清掉悬空引用后只剩标题的小节被删掉，上游本来就空的
  小节保持原样。
- **上游资产池内部的小节会被整段删除**：上游技能里引用本 fork 不随附的 harness 文件的
  章节（例如 docker-patterns 的 ECC plugin setup 段）会被整段删掉，免得模型去找
  不存在的路径。

判定逻辑只有一份：`tools/refscan.py`。物化器用它来改写，`tools/check_refs.py`
用它来卡门禁 —— 两边不会各写一套启发式而互相漂移。门禁对
`skills/ commands/ agents/ rules/ own/` 全量扫描，有悬空引用就退出码 1。

---

## 与 omp 的适配点

| omp 机制 | 本 fork 的做法 |
| --- | --- |
| skill 发现 | `<root>/skills/<name>/SKILL.md`，非递归一层。物化时保证 frontmatter 有 `name` + `description` |
| command 发现 | 本 fork 不发布命令；上游的 24 个 command 快照只留在 `pool/` 里，不物化 |
| agent 发现 | `<root>/agents/*.md`，裸名注册（`forge-java-reviewer` …）。**物化时剥掉 `model: sonnet\|opus\|haiku`** —— omp 无这些别名，留着会让 agent 解析不到模型而不可用 |
| rule 发现 | `<root>/rules/*.md`，带 `description` 的进 rulebook（system prompt 列名 + 描述，正文按需 `rule://` 读）；**不使用 `alwaysApply`**，避免每轮全文注入 |
| 工具名 | 上游 ECC 规则与 skill 里残留的 Claude Code 工具名（`TodoWrite` / `Task(subagent_type=)` / `Agent(`）由 fork 规则 `omp-tooling` 给出 omp 对照表 |
| 提示行里的描述 | omp 会把过长的 skill 描述压短后写进系统提示，压缩结果缓存在 `~/.omp/agent/skill-descriptions.db`；所以提示行不等于 frontmatter，判定归属用 `omp skill list` 的完整描述 |
| 真正重名的资产 | 加 `forge-` 前缀后本 fork 的资产不再与 omp 内建同名（本仓 `forge-java-reviewer` vs 内建 `reviewer`、`scout` 一类），也不与别的插件重名；外部插件提供的资产（如 `code-review` skill）仍按它自己的名字解析 |

fork 自有的 5 条 rules：

| 规则 | 管什么 |
| --- | --- |
| `omp-tooling` | omp 的工具名与上游 Claude 写法的对照表；改文件用 `edit` 不用 `write` 等硬约定 |
| `omp-delegation` | 本 fork 的 agent 清单、委派与并行的纪律 |
| `fork-workflow` | 先查再写 → 先计划再实现 → 验证后再声明完成 → 收尾 |
| `fork-verification` | 测试覆盖口径（以项目自身门槛为准）、回归测试范围、密钥与外部内容处理 |
| `fork-coding-style` | 跟随项目既有风格优先于通用原则；不可变优先；注释写「为什么」 |

---

## 许可与出处

上游 ECC 为 MIT 许可，版权归 Affaan Mustafa（见 `LICENSE`）。本 fork 保留原许可，
改动仅为「裁剪 + omp 适配 + 去掉 Claude 专有字段」，详见 `NOTICE.md`。
