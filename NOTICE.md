# NOTICE

本仓库是 [Everything Claude Code (ECC)](https://github.com/affaan-m/ECC) 的派生作品。

- 上游许可：MIT，版权归 Affaan Mustafa（完整文本见 `LICENSE`）。
- 上游版本：2.2.3
- 上游 commit：`07971588f8ac7a60080ba8c1b7920c9e8e733e7d`（2026-10-20）
- 上游内容来源：仓库的 `pi/core/`（132 skills + 24 commands，官方为 Pi 生态生成的精简档）
  与 `agents/`（71 个 agent 定义）。

## 本 fork 的改动

1. **裁剪**：`pool/` 保留上游全量快照，`skills/` `commands/` `agents/` 只物化被选中的部分。
2. **omp 适配**：
   - 移除 agent frontmatter 的 `model: sonnet|opus|haiku`（Claude 专有别名，omp 无对应模型，
     保留会导致 agent 无法解析模型而不可用）。
   - agent frontmatter 的 `tools:` 归一化为 omp 的工具名，丢弃 Claude 专有工具
     （`WebFetch` / `NotebookEdit` / `SlashCommand` 等）。
   - `package.json` 保留上游 `pi.skills` / `pi.prompts` 声明，omp 的 `omp-plugins` provider
     据此发现 `skills/` 与 `commands/`。
3. **正文改写**（由 `tools/apply_selection.py` 在物化时确定性执行，`tools/check_refs.py`
   用同一套判定做门禁）：
   - Claude 专有工具名与交互机制（`AskUserQuestion`、`TodoWrite`、`PreToolUse` hook 等）
     换成 omp 的对应写法。
   - 路径约定：`CLAUDE.md` → `AGENTS.md`，`.claude/prds/` → `docs/prds/` 等。
   - **悬空引用清除**：指向本 fork 不提供的资产（上游全量 ECC 才有的命令、被当前 profile
     排除的兄弟 skill、嵌套 `rules/react/*.md`、上游 `docs/`）的引用会被删除；指向可读资产的
     相对 markdown 链接会改写成 omp 能跟随的规范 URI（`skill://<name>` 等）。
4. **工具化**：新增 `tools/`（上游更新、重放选择、部署、生成目录、引用门禁）。

正文改动由脚本确定性生成，`pool/` 中的上游快照保持原样，便于逐条比对。

