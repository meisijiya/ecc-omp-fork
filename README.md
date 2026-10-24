# ecc-omp-fork

> ECC（[affaan-m/ECC](https://github.com/affaan-m/ECC)）的 **omp 编程子集 fork**。
> 把 ECC 里跟编程相关的能力抽出来，做成可版本化、可增量更新的独立 omp 插件，
> 同时把每轮系统提示的 token 开销压到可控范围。

本仓库是**唯一事实源**。运行态安装目录（`~/.omp/agent/local/ecc-omp-fork`）由
`tools/deploy.py` 从这里同步过去，omp 通过 `omp plugin link` 指向该安装目录。

默认 profile（`java-python`）下的生效规模：**68 skills + 24 commands + 31 agents + 5 rules**
（68 = 上游选中的 67 个 skill + 本 fork 自带的 `ecc-omp-router`）；换 profile 后的规模见
「切换 profile」一节的表。

---

## 在 omp 中安装与配置

### 一条命令装好

```bash
git clone https://github.com/meisijiya/ecc-omp-fork.git
cd ecc-omp-fork
python tools/apply_selection.py     # 按当前 profile 物化 skills/commands/agents/rules
python tools/build_catalog.py        # 刷新 docs/CATALOG.md（可选，但建议跟上游一起提交）
python tools/deploy.py              # 同步到 omp 安装目录并 link
```

`deploy.py` 做四件事：

1. 校验 `manifest/applied.json` 里的 profile 与 `manifest/selection.json` 的
   `active_profile` 是否一致（不一致直接退出，提示先跑 `apply_selection.py`）；
2. 把 `skills/ commands/ agents/ rules/` 同步到 `~/.omp/agent/local/ecc-omp-fork`，
   并额外拷贝 `package.json` / `LICENSE` / `NOTICE.md`；
3. 执行 `omp plugin link ~/.omp/agent/local/ecc-omp-fork`（重复 link 是安全的，不会报错），
   再跑一次 `omp plugin list`；
4. 用 `omp skill list` 校验物化出来的 skill 是否都被 omp 认到，对不上会打印清单并以
   退出码 1 结束（`--skip-verify` 可跳过这一步校验）。

顺带还会清掉早期布局留下的旧插件（`ecc-pi-core` / `ecc-programming`）：残留的 junction
会让同一批 skill 被注入系统提示两次，所以 `deploy.py` 每次都会顺手 uninstall + 删目录。

`omp plugin link` 在 Windows 上建的是**目录 junction**，目标是
`~/.omp/plugins/node_modules/ecc-omp-fork`，它指向安装目录
`~/.omp/agent/local/ecc-omp-fork`（安装目录里必须有 `package.json`，插件名取自其中的
`name: ecc-omp-fork`）。链接关系可以直接查：

```bash
ls -l ~/.omp/plugins/node_modules/ecc-omp-fork     # 应显示指向 .omp/agent/local 的链接
omp plugin list                                     # 应能看到 ecc-omp-fork@0.1.0
```

装完后在 omp 里：

- 技能：`read skill://<name>`，例如 `read skill://ecc-omp-router`
- 规则：`read rule://<name>`，例如 `read rule://fork-workflow`
- 命令：直接敲 `/plan`、`/code-review`、`/test-coverage`、`/pr`
- 子代理：`task` 的 `agent` 字段填**裸名**，例如 `code-reviewer`、`java-reviewer`

改完资产后在 omp 会话里跑 `/reload-plugins`（技能与命令即时刷新），
**agent 需要重开会话**才被发现。

### 手工安装（不想用脚本）

```bash
git clone https://github.com/meisijiya/ecc-omp-fork.git
cd ecc-omp-fork
python tools/apply_selection.py
# 把 skills/ commands/ agents/ rules/ package.json 复制到任意目录，例如：
mkdir -p ~/.omp/agent/local/ecc-omp-fork
cp -r skills commands agents rules package.json ~/.omp/agent/local/ecc-omp-fork/
omp plugin link ~/.omp/agent/local/ecc-omp-fork
```

`omp plugin link <目录>` 直接把该目录挂进 `~/.omp/plugins/node_modules/<package name>`，
Windows 下是 junction。装完同样要 `/reload-plugins` 才在会话里生效。

### 启用与禁用（语义与自证）

本插件贡献的资产分四类：**skill / command / rule / agent**。它们同属一个插件根目录，
所以启停是**整体生效**的——不是「只关 skill、其余照旧」：

```bash
omp plugin disable ecc-omp-fork    # 四类资产一起从 omp 的发现结果里消失
omp plugin enable  ecc-omp-fork    # 恢复
```

- CLI 改完之后要 `/reload-plugins` 才会刷新当前会话的 skills / 斜杠命令 / task agents / MCP；
  在 omp 的 TUI 里用 `/plugins enable|disable` 则会立刻刷新当前会话。
- 禁用只影响**本插件**提供的资产。若某个名字同时由别的来源提供（别的插件，或 omp
  自带的同名内置资产，例如 `security-reviewer`），禁用本插件后该名字仍会解析到别人的
  那份 —— 那是同名冲突，不是本插件残留。

自证脚本会自己跑一遍「禁用 → 探测 → 启用 → 探测」，并在 `finally` 里把插件恢复到
**执行前的原状态**（原来禁用就还禁用）：

```bash
python tools/check_plugin_isolation.py --toggle-test
```

- `--toggle-test`：临时禁用/启用本插件，验证四类资产在两种状态下的可见性是否符合预期。
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
再写进提示行，压缩结果缓存在 `~/.omp/agent/skill-descriptions.db`。所以本仓 68 个 skill
里有 44 个在提示行里显示的是压缩后的短句（`omp skill list` 里仍是完整描述）——它们照样
属于本插件。判定规则：

| 观察 | 含义 |
| --- | --- |
| 名字被提示，且 `omp skill list` 里是本仓的描述 | 本插件的资产（提示行可能是压缩过的短句） |
| 名字被提示，但 `omp skill list` 里不是本仓的描述 | 同名冲突：这个名字归别人 |
| 名字不被提示 | 本插件没有提供它 |

当前唯一真实的同名冲突是 omp 内建的 `security-reviewer` agent：插件启用时本仓版本胜出，
禁用后由内建版本接管。skill 侧没有重名。

判定「本插件有没有泄漏」靠的是差值而不是名字表：提示行里的 skill 条目数在启用态是 243、
禁用态是 175，差值 68 正好等于本仓的 skill 总数，且少掉的正是这 68 个名字；同一轮探测里
`omp skill list` 从 ours=68 变成 ours=0。commands 24、rules 5、agents 31 是逐条按描述比对过的。

### 卸载

```bash
# 方式一：脚本（会先跑 omp plugin uninstall，再删安装目录）
python tools/deploy.py --uninstall

# 方式二：手工
omp plugin uninstall ecc-omp-fork
rm -rf ~/.omp/agent/local/ecc-omp-fork
```

`omp plugin uninstall` 会移除 `~/.omp/plugins/node_modules/ecc-omp-fork` 里的链接，
并清掉 lockfile 里的运行时状态。安装目录 `~/.omp/agent/local/ecc-omp-fork` 是本仓
`deploy.py` 生成的产物，`omp plugin uninstall` 不会碰它，需要自己删
（或用 `python tools/deploy.py --uninstall` 一步删掉：它先跑 `omp plugin uninstall`，
再 `rmtree` 安装目录）。

注意：**link 型插件不会出现在 `~/.omp/plugins/installed_plugins.json`** —— 那个文件只记
marketplace 安装的插件。link 型插件的启停状态记在
`~/.omp/plugins/omp-plugins.lock.json`（形如
`"ecc-omp-fork": {"version":"0.1.0","enabledFeatures":null,"enabled":true}`）。

### 升级

```bash
git pull
python tools/apply_selection.py     # 上游文本变了就重新物化
python tools/build_catalog.py        # 刷新 docs/CATALOG.md
python tools/deploy.py               # 同步到安装目录并重新 link
```

然后在 omp 会话里 `/reload-plugins`：**skills / 斜杠命令即时生效，新增的 agent 需要开一个
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

| profile | skills | commands | agents | 适用 |
| --- | --- | --- | --- | --- |
| `java-python` | 67 | 24 | 31 | 默认。Java/Kotlin + Python/Django/FastAPI + 通用工程规范 |
| `lite` | 43 | 15 | 14 | 每轮提示开销最低，只做后端核心 |
| `full` | 132 | 24 | 58 | 上游 `pi/core` 全量 + 全部编程 agent，冷门技术栈时用 |

表中数字是各 profile 从上游 `pool/` **选中的资产数**，不含本 fork 自带资产：物化后实际生效的
skills 数 = 上表数字 + 1（自有 `ecc-omp-router`），commands / agents 与上表一致，rules 恒为自有 5 条。

各 profile 的收益对比（技能描述进系统提示的部分）：

| profile | 技能描述字符数 | 约合 token |
| --- | --- | --- |
| ECC 全量上游 | 95,615 | ~24K |
| `full` | 38,178 | ~9.5K |
| `java-python` | 18,904 | ~4.7K |
| `lite` | 13,037 | ~3.3K |

数字口径：各 profile **选中的上游 skill** 的 frontmatter `description` 字符数（按当前
`pool/` 快照实测），约 4 字符 = 1 token；「ECC 全量上游」一行沿用上游自己的口径。
`full` 物化后实际进系统提示的是 133 个 skill（132 个上游 + 自有 `ecc-omp-router`），
合计 38,349 字符，约 ~9.6K token。

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
`full` / `java-python` / `lite` 三个 profile 依次物化 + 校验。

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

### 门禁清单

| 命令 | 查什么 | 退出码 | 什么时候跑 |
| --- | --- | --- | --- |
| `python tools/check_refs.py [--json]` | **引用自洽**：物化树与 `own/` 里是否还有指向「本 fork 不提供的资产」的悬空引用（`skill://`、`skills/<name>/`、`commands\|agents\|rules/<name>.md`、斜杠命令、反引号裸名） | 0 = 无缺陷悬空（fork 自有目录里的 profile 裁剪引用只列出、不算缺陷）；1 = 有缺陷悬空（打印明细）；2 = profile 指针读不出来（`active_profile` 缺失或未知） | 每次改完物化树或上游文本后；提交前必跑 |
| `python tools/check_adapt.py [--tree <dir>] [--json]` | **omp 适配不变式**：INV-01..INV-15（无 `model:`、无 `CLAUDE.md`、无 `.claude/`、无 Claude CLI 调用、无 Claude 工具名、skill/agent/rule/command 的 frontmatter 完整性、`/name` 引用必须落在物化 commands 名单内、无「Claude Code」措辞等） | 0 = 无违规；1 = 有违规（逐条给 `文件:行号` + token）；2 = 用法错误或树不可读 | 每次改完物化树后；提交前必跑 |
| `python tools/check_upstream_pin.py` | **上游 pin 一致性**：`manifest/upstream.json` 形状（`commit` 必须是 40 位小写 hex、`repo` 非空）、`manifest/groups.json` 的 upstream.commit 镜像与 pin 一致、`pool/` 摘要等于 pin 的 `pool_digest` | 0 = 三项全过；1 = 有校验项不符（逐条打印）；2 = `manifest/upstream.json` / `manifest/groups.json` 读不出来 | 每次同步上游之后；提交前必跑 |
| `python tools/check_plugin_isolation.py [--probe\|--toggle-test] [--omp <path>] [--cwd <dir>] [--root <dir>] [--json]` | **插件启停可见性**：本插件四类资产在启用态是否被 omp 提供、禁用态是否全部消失 | 0 = 符合预期；1 = 不一致（打印 FAIL 明细）；2 = 工具错误 | 改了部署方式、插件启停状态或 omp 版本之后 |

补充说明：

- `check_refs.py` 与 `check_adapt.py` 都是**检测型**门禁，只读不改物化树。
- **profile 裁剪与悬空引用的分界**：上游正文在物化时会把当前 profile 没有的资产引用删掉，
  所以物化树里剩下的「裁剪引用」只可能出现在 fork 自有的目录文件（`own/skills/`、`own/rules/`
  及其物化副本）——那两份文件描述的是整个 fork 的目录，本来就会点名别的 profile 的资产。
  这类引用被单独列出（`check_refs.py` 的 `profile_cropped_in_fork_catalog`），
  但不算缺陷；名字在 `pool/` 里根本不存在的引用在任何文件里都仍然是缺陷。
  `check_adapt.py` 的 INV-14 用同一条分界。
- `check_adapt.py` 只扫物化树 `skills/ commands/ agents/ rules/`（含子目录里的脚本文件），
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

### 其他可选配置

```bash
# 只加载指定技能（omp 全局设置，会影响其它插件的技能）
# ~/.omp/agent/config.yml
skills:
  includeSkills:
    - "java-*"
    - "python-*"
    - "springboot-*"
```

```yaml
# 隐藏个别技能的描述（仍可用 skill:// 读取，只是不进系统提示列表）
# skills/<name>/SKILL.md 的 frontmatter 加一行：
hide: true
```

---

## 目录结构

| 路径 | 作用 |
| --- | --- |
| `pool/skills/` | 上游 ECC `pi/core` 的 132 个 skill 快照（未裁剪） |
| `pool/commands/` | 上游 ECC `pi/core` 的 24 个 command 快照 |
| `pool/agents/` | 上游 ECC `agents/` 的 71 个 agent 快照（原始，含 Claude 专有 `model:` 行） |
| `own/skills/` | fork 自有 skill（`ecc-omp-router` 选路表），始终物化 |
| `own/rules/` | fork 自有 rules（5 条 omp 适配规则），始终物化 |
| `manifest/groups.json` | 三类资产的分类目录（分组 → 成员）；顶层 `upstream` 块是上游 pin 的同步镜像 |
| `manifest/profiles/` | profile 定义（组 + 排除项） |
| `manifest/selection.json` | 当前 profile 指针 + 额外追加项 |
| `manifest/applied.json` | 上次物化实际生效的 profile 与数量（部署前用来校验是否过期） |
| `manifest/upstream.json` | 上游 pin 唯一事实源：`repo` / `commit` / `version` / `pool_digest` |
| `manifest/external_refs.json` | 本 fork 不提供、但由别的 omp 插件提供的资产（如 `code-review` skill） |
| `skills/` `commands/` `agents/` `rules/` | **物化后的实际生效内容**（入库，便于 diff 上游变更） |
| `tools/` | 更新、裁剪、部署、生成目录、各项门禁的脚本 |
| `.github/workflows/sync-upstream.yml` | 定时 / 手动上游同步，自动开 PR 并跑全套门禁 |
| `docs/CATALOG.md` | 人类可读的资产目录（生成物） |

---

## 常用命令

```bash
# 抓取上游最新 ECC，刷新 pool，重放选择，打印变更摘要
python tools/sync_upstream.py

# 只刷新 pool（不重放选择）
python tools/sync_upstream.py --pool-only

# 按当前 profile 重新物化 skills/ commands/ agents/ rules/
python tools/apply_selection.py

# 引用门禁：检查是否还有指向「本 fork 不提供的资产」的引用
python tools/check_refs.py

# 适配门禁：检查 omp 适配不变式（INV-01..INV-15）
python tools/check_adapt.py

# 上游 pin 门禁：检查 pin / 镜像 / pool 摘要三者一致
python tools/check_upstream_pin.py

# 插件隔离自证：临时禁用→探测→启用→探测（finally 恢复原状态）
python tools/check_plugin_isolation.py --toggle-test

# 只观察当前插件可见性，不改变状态
python tools/check_plugin_isolation.py --probe

# 部署到 omp 的安装目录并 link
python tools/deploy.py

# 部署但跳过 omp skill list 校验
python tools/deploy.py --skip-verify

# 卸载：omp plugin uninstall + 删除安装目录
python tools/deploy.py --uninstall

# 重新生成资产目录文档
python tools/build_catalog.py
```

### 上游正文会被改写

`pool/` 里的上游快照是原样，但物化到 `skills/` `commands/` `agents/` 时会做**确定性改写**：

- Claude 专有工具名与机制 → omp 的对应写法（`AskUserQuestion` → `ask`、
  `TodoWrite` → `todo`、删掉 `PreToolUse` hook 段等）。
- 路径约定（`CLAUDE.md` → `AGENTS.md`、`.claude/prds/` → `docs/prds/`）。
- **agents 走同一条改写通道**：agents 与 skills/commands 一样做工具名与路径改写，
  只是 agents 侧的 `Task` 改名规则被剔除 —— C#/Swift 的 `Task` 是类型名，改了会坏掉。
- **悬空引用清除**：指向本 fork 不提供的资产（上游全量 ECC 才有的命令、被当前 profile
  排除的兄弟 skill、嵌套 `rules/react/*.md`、上游 `docs/`）的引用会被删掉；
  指向可读资产的相对 markdown 链接会被改写成 omp 能跟随的规范 URI
  （`[react-testing](../react-testing/SKILL.md)` → `skill://react-testing`）。
- **带 kind 前缀的引用**也会被识别并改写：`` `skill: foo` `` → `skill://foo`，
  ``rules: `foo/bar` `` 这类写法在指向可读资产时同样改成规范 URI；指向本 fork
  未提供的资产的会被剪掉。
- **变空的小节标题会一并删除**：清掉悬空引用后只剩标题的小节被删掉，上游本来就空的
  小节保持原样。
- **上游仓库内部的小节会被整段删除**：上游技能里引用本 fork 不随附的 harness 文件的
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
| command 发现 | `<root>/commands/*.md`，裸名注册（`plan` / `pr` / `code-review` …） |
| agent 发现 | `<root>/agents/*.md`，裸名注册。**物化时剥掉 `model: sonnet\|opus\|haiku`** —— omp 无这些别名，留着会让 agent 解析不到模型而不可用 |
| rule 发现 | `<root>/rules/*.md`，带 `description` 的进 rulebook（system prompt 列名 + 描述，正文按需 `rule://` 读）；**不使用 `alwaysApply`**，避免每轮全文注入 |
| 工具名 | 上游 ECC 规则与 skill 里残留的 Claude Code 工具名（`TodoWrite` / `Task(subagent_type=)` / `Agent(`）由 fork 规则 `omp-tooling` 给出 omp 对照表 |
| 提示行里的描述 | omp 会把过长的 skill 描述压短后写进系统提示，压缩结果缓存在 `~/.omp/agent/skill-descriptions.db`；所以提示行不等于 frontmatter，判定归属用 `omp skill list` 的完整描述 |
| 真正重名的资产 | 目前只有 `security-reviewer` agent 与 omp 内建同名：插件启用时本仓版本胜出，禁用后由内建版本接管。skill 侧没有重名；`skill://<name>` 始终解析到**本插件的文件** |

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
