# ecc-omp-fork

> ECC（[affaan-m/ECC](https://github.com/affaan-m/ECC)）的 **omp 编程子集 fork**。
> 把 ECC 里跟编程相关的能力抽出来，做成可版本化、可增量更新的独立 omp 插件，
> 同时把每轮系统提示的 token 开销压到可控范围。

本仓库是**唯一事实源**。运行态安装目录（`~/.omp/agent/local/ecc-omp-fork`）由
`tools/deploy.py` 从这里同步过去，omp 通过 `omp plugin link` 指向该安装目录。

当前生效规模：**68 skills + 24 commands + 31 agents + 5 rules**（profile `java-python`；68 = 上游选中的 67 个 skill + 本 fork 自带的 `ecc-omp-router`）。

---

## 在 omp 中安装与配置

### 一条命令装好

```bash
git clone https://github.com/meisijiya/ecc-omp-fork.git
cd ecc-omp-fork
python tools/apply_selection.py     # 按当前 profile 物化 skills/commands/agents/rules
python tools/deploy.py              # 同步到 omp 安装目录并 link
```

`deploy.py` 做三件事：把 `skills/ commands/ agents/ rules/ package.json` 复制到
`~/.omp/agent/local/ecc-omp-fork`，然后 `omp plugin link` 该目录。
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

### 切换 profile（改变每轮 token 开销）

profile 定义在 `manifest/profiles/`，当前指针在 `manifest/selection.json` 的
`active_profile` 字段。

```bash
# 1) 改指针
#    manifest/selection.json: "active_profile": "lite"
# 2) 重新物化并部署
python tools/apply_selection.py
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
| `full` | 36,905 | ~9.2K |
| `java-python` | 18,074 | ~4.5K |
| `lite` | 12,207 | ~3.1K |

数字口径：各 profile **选中的上游 skill** 的 frontmatter `description` 字符数，约 4 字符 = 1 token；
「ECC 全量上游」一行沿用上游自己的口径。

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
| `manifest/groups.json` | 三类资产的分类目录（分组 → 成员） |
| `manifest/profiles/` | profile 定义（组 + 排除项） |
| `manifest/selection.json` | 当前 profile 指针 + 额外追加项 |
| `manifest/applied.json` | 上次物化实际生效的 profile 与数量（部署前用来校验是否过期） |
| `manifest/external_refs.json` | 本 fork 不提供、但由别的 omp 插件提供的资产（如 `code-review` skill） |
| `skills/` `commands/` `agents/` `rules/` | **物化后的实际生效内容**（入库，便于 diff 上游变更） |
| `tools/` | 更新、裁剪、部署、生成目录、引用门禁的脚本 |
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

# 部署到 omp 的安装目录并 link
python tools/deploy.py

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

`tools/sync_upstream.py` 的上游源解析顺序：
`.upstream/` 本地克隆 → omp marketplace 缓存克隆（`~/.omp/plugins/cache/marketplaces/ecc`）
→ 新克隆到 `.upstream/`。Windows 上 git 走 HTTP/2 容易中途断流，脚本对 clone 与 fetch
两条路径都强制 `http.version=HTTP/1.1`。

---

## 与 omp 的适配点

| omp 机制 | 本 fork 的做法 |
| --- | --- |
| skill 发现 | `<root>/skills/<name>/SKILL.md`，非递归一层。物化时保证 frontmatter 有 `name` + `description` |
| command 发现 | `<root>/commands/*.md`，裸名注册（`plan` / `pr` / `code-review` …） |
| agent 发现 | `<root>/agents/*.md`，裸名注册。**物化时剥掉 `model: sonnet|opus|haiku`** —— omp 无这些别名，留着会让 agent 解析不到模型而不可用 |
| rule 发现 | `<root>/rules/*.md`，带 `description` 的进 rulebook（system prompt 列名 + 描述，正文按需 `rule://` 读）；**不使用 `alwaysApply`**，避免每轮全文注入 |
| 工具名 | 上游 ECC 规则与 skill 里残留的 Claude Code 工具名（`TodoWrite` / `Task(subagent_type=)` / `Agent(`）由 fork 规则 `omp-tooling` 给出 omp 对照表 |

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
