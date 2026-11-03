---
name: forge-absorb-third-party-skill
description: 把第三方仓库的 skill 收纳进本插件的 absorbed 池：筛条、pin、声明式改写、profile 分流、七门禁验证与已知坑
---

# 往本插件收纳第三方 skill

适用：要把 fork 之外仓库的 skill 纳入本仓，且必须能按上游版本同步、按 profile 分流、过门禁。

## 硬约束（先确认，别试）

| 落点 | 结果 |
|---|---|
| `pool/` | `check_upstream_pin` 红：池摘要由 `compute_pool_digest()` 算，内容变即不符 |
| `own/skills/` | `apply_selection.py` 对所有 profile 无条件 `copytree`，无法按 profile 裁剪；且无上游 sha |
| `absorbed/<source>/` | ✅ 唯一可行：独立 pin + 摘要 + 改写规则，profile 用独立 `"absorbed": [...]` 字段 |

## 步骤

1. **筛条**：按「独立（无设置文件/agents/playbooks/兄弟 skill 硬引用）+ 与本仓现有资产、
   其它已装插件不重叠」判。兄弟 skill 引用要用正则扫 `../<name>/SKILL.md`、
   `Apply the **<name>**`、"in this pack"，不能只看 description。
2. **pin 来源**：`git ls-remote <repo> HEAD` 取 40 位 sha（GitHub API 无 token 会 403）。
3. **写 `manifest/absorbed.json`**：`sources.<slug>{repo,commit,license{file,copyright}}`、
   `skills.<name>{source,path,exclude[]}`、`bundle{skill,source,path,from[]}`。
4. **写 `tools/absorbed_fixups.py` 规则**：
   - 逐文件规则 `key = "<slug>/<path>"`，形如 `(find_regex, replace, note)`，必须恰好命中 1 次；
   - 整源批量规则写进 `SOURCE_RULES`，形如 `(find, replace, note, expected_total)`，
     `expected_total` 是整源命中总数，由 `verify_source_counts()` 校验；
   - 必改几类：斜杠触发词（本插件不发布命令，INV-14）、别的 harness 的目录与常驻指令文件
     写法（INV-02/03）、别的 harness 的名字、宿主专用的 frontmatter 键（禁自动调用开关与
     路径限定键）、兄弟 skill 链接、
     以及指向共享底座的相对路径（改成 `skill://<runtime>/<file>`）。
5. **`python tools/sync_absorbed.py`**：拉 pin → 重放规则 → 落盘 → 刷 sha256 → 生成 bundle。
   规则命中数不符会失败——这就是上游改写检测，改规则而不是改生成物。
6. **profile 分流**：改 `manifest/profiles/<p>.json` 的 `"absorbed": [...]`，不要塞 `include`
   （`resolve()` 会去 pool 查而报「selected but not present in pool」）。
7. **验证**：`apply_selection` → `check_adapt` → `check_refs` → `check_upstream_pin` →
   `check_absorbed` → `check_zh_descriptions` → `upstream_versions check --offline` →
   `build_catalog` → `deploy` → `check_plugin_isolation --toggle-test`，三个 profile 各跑一遍。

## 踩过的坑

- **description 里的 `\"` 会让 isolation 判 conflict**：`check_plugin_isolation.py:frontmatter()`
  只剥外层引号、不处理 YAML 转义，omp 列出的却是解码后文本。改用中文引号「」。
- **不要 `python tools/apply_selection.py | head`**：Windows 上管道提前关闭抛
  `OSError: [Errno 22]`，会在写 `manifest/applied.json` 之前中断。
- **`refscan.pool_sets()` 必须并入收纳名**（读 `manifest/absorbed.json`），否则未物化的收纳资产判
  `unknown` 而非 `cropped`，`fork_owned` 豁免失效 → lite 门禁红。
- **`refscan.source_exists()` 必须探 `absorbed/`**：否则收纳 skill 里的相对链接被判悬空，
  物化时整行被删，内容静默丢失。吸收条目在物化期不允许出现 drop 动作（`apply_selection.py`
  会直接失败）。
- **NOTICE.md 只能有 1 个 40 位 sha**（`check_upstream_pin.py`）：收纳 commit 只进 manifest；
  同时补上游 LICENSE 到 `absorbed/<source>/LICENSE` 并在 NOTICE 加归属节
  （MIT 要求版权与许可声明随内容）。
- **生成物不要手改**：bundle 由 `sync_absorbed.py` 从快照拼接，`check_absorbed` 比对生成物与其输入。
- 新 skill 需重载会话才出现在 `skill://` 索引；`omp skill list` 即时可见。
