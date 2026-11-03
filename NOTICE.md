# NOTICE

本仓库是 [Everything Claude Code (ECC)](https://github.com/affaan-m/ECC) 的派生作品。

- 上游许可：MIT，版权归 Affaan Mustafa（完整文本见 `LICENSE`）。
- 上游版本：2.2.3
- 上游 commit：`b38be6a7f6350964d59328b52f0624e1d1d552d1`（与 `manifest/upstream.json` 的 pin 一致）
- 上游内容来源：仓库的 `pi/core/`（134 skills + 24 commands，官方为 Pi 生态生成的精简档）
  与 `agents/`（71 个 agent 定义）。

## 本 fork 的改动

1. **裁剪**：`pool/` 保留上游全量快照，`skills/` `agents/` 只物化被选中的部分。
   物化出来的 skill / agent 统一带 `forge-` 前缀（上游名不带），前缀只用于
   与别的插件的同名资产区分；`pool/` 与 `manifest/` 里保留上游名。
   本 fork **不发布命令**：上游的 24 个 command 只留在 `pool/` 里，不物化。
2. **omp 适配**：
   - 移除 agent frontmatter 的 `model: sonnet|opus|haiku`（Claude 专有别名，omp 无对应模型，
     保留会导致 agent 无法解析模型而不可用）。
   - agent frontmatter 的 `tools:` 归一化为 omp 的工具名，丢弃 Claude 专有工具
     （`WebFetch` / `NotebookEdit` / `SlashCommand` 等）。
   - `package.json` 保留上游 `pi.skills` 声明，omp 的 `omp-plugins` provider
     据此发现 `skills/`。
3. **正文改写**（由 `tools/apply_selection.py` 在物化时确定性执行，`tools/check_refs.py`
   用同一套判定做门禁）：
   - Claude 专有工具名与交互机制（`AskUserQuestion`、`TodoWrite`、`PreToolUse` hook 等）
     换成 omp 的对应写法。
   - 路径约定：`CLAUDE.md` → `AGENTS.md`，`.claude/prds/` → `docs/prds/` 等。
   - **悬空引用清除**：指向本 fork 不提供的资产（上游全量 ECC 才有的命令、被当前 profile
     排除的兄弟 skill、嵌套 `rules/react/*.md`、上游 `docs/`）的引用会被删除；指向可读资产的
     相对 markdown 链接会改写成 omp 能跟随的规范 URI（`skill://<name>` 等）。
   - **资产名改写**：指向被改名资产的引用（`skill://api-design` → `skill://forge-api-design`、
     反引号裸名 → 带前缀的运行名）会一并改写；散文里不是资产引用的普通词不动。
4. **工具化**：新增 `tools/`（上游更新、重放选择、部署、生成目录、引用门禁）。
5. **自有资产**：`own/skills/` 下除选路表 `forge-router` 外，另有六条本 fork 原创的 skill
   ——发布与运维三条（`forge-release-management`、`forge-observability`、
   `forge-incident-response`），插件自身的运维三条（`forge-pipeline`、`forge-ci-triage`、
   `forge-absorb-third-party-skill`），随 fork 一起分发（MIT）。
   第三方正文见下节「第三方收纳资产」。

正文改动由脚本确定性生成，`pool/` 中的上游快照保持原样，便于逐条比对。

## 第三方收纳资产

`absorbed/` 下的 skill 来自三个 MIT 许可的仓库，经 `tools/absorbed_fixups.py` 的声明式
规则改写后随本 fork 发布。来源 commit、逐文件摘要与许可声明记在 `manifest/absorbed.json`，
刷新用 `python tools/sync_absorbed.py`；决策记录见
`docs/adr/0010-absorbed-pool-for-third-party-skills.md`。

| 来源 | 许可 | 随附文本 |
| --- | --- | --- |
| [backnotprop/pstack](https://github.com/backnotprop/pstack) | MIT，Copyright (c) 2026 Lauren Tan | `absorbed/pstack/LICENSE` |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | MIT，Copyright (c) 2025 Addy Osmani | `absorbed/addyosmani/LICENSE` |
| [fishzjp/qa-skills](https://github.com/fishzjp/qa-skills) | MIT，Copyright (c) 2026 fishzjp | `absorbed/qa-skills/LICENSE` |

收纳池共 19 条，进入运行树的是 18 条：

- pstack 与 addyosmani：`forge-correct`、`forge-sharpen`、`forge-engineering-principles`
  （由 8 份 principle 快照拼接生成）、`forge-constraint-driven-development`、
  `forge-statechart`。`forge-constraint-driven-development` 与 `forge-statechart` 只进
  `full` profile；pstack 的 `forge-typescript-best-practices` 留在收纳池里但不再物化，
  它的职责由 ECC 上游的 `forge-typescript-patterns` 承担（同一件事只留一个入口）。
- qa-skills 的 QA 套件：`forge-qa`、`forge-requirement-analysis`、`forge-test-strategy`、
  `forge-test-case-writing`、`forge-test-case-review`、`forge-exploratory-testing`、
  `forge-automated-e2e-testing`、`forge-api-testing`、`forge-bug-analysis`、
  `forge-regression-testing`、`forge-test-reliability`、`forge-qa-memory`，以及承载它们
  共享方法、模板与校验脚本的依赖单元 `forge-core`。整套进 `full` 与 `java-python`，
  `lite` 一条不收纳（正文里指向未启用 skill 的反引号裸名会降级为 notice，见
  `docs/adr/0014-qa-skills-absorption.md`）。

### 许可正文

本插件分发的 `NOTICE.md` 自身即携带下列许可全文（MIT 要求版权声明与许可正文随副本分发）。

#### backnotprop/pstack

```
MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### addyosmani/agent-skills

```
MIT License

Copyright (c) 2025 Addy Osmani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### fishzjp/qa-skills

```
MIT License

Copyright (c) 2026 fishzjp

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
