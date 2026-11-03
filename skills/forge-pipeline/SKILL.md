---
name: forge-pipeline
description: 同步上游、发布或部署本插件时用：七个门禁的顺序、三个 profile 的规模、Windows 的 CRLF 与管道坑、发布后要验的东西
---

# 本插件的更新与发布流水线

改动本仓（插件 id 是 omp-skill-forge）后按这个顺序跑，全绿才算完成。门禁顺序有意义：物化在前，
检测在后，最后才部署。

## 门禁（顺序有意义）

```bash
python tools/apply_selection.py       # 物化当前 profile 的运行树
python tools/build_catalog.py          # 刷新 docs/CATALOG.md
python tools/check_refs.py             # 悬空引用
python tools/check_adapt.py            # omp 适配不变式 INV-01..15
python tools/check_upstream_pin.py     # 上游 pin 与 pool 摘要
python tools/check_absorbed.py         # 收纳池：pin、摘要、生成物、许可、CRLF、残留
python tools/check_zh_descriptions.py  # 每条 skill 与 agent 的中文触发描述
python tools/upstream_versions.py check --offline   # 逐资产版本台账的形状与覆盖
python tools/check_plugin_isolation.py --toggle-test # 启停可见性（本地，会切换插件）
python tools/deploy.py                 # 同步到 ~/.omp/agent/local/omp-skill-forge
```

CI（`.github/workflows/sync-upstream.yml`）会按 full、java-python、lite 三个 profile 依次跑
apply_selection + check_adapt + check_refs，最后还原成已提交的 profile。改了 profile 数组
或吸收条目，本地也要照这个循环跑一遍，跑完 `git checkout -- manifest/selection.json`
再重新物化。

## 三个 profile 的物化规模

| profile | skill | 组成 |
| --- | --- | --- |
| java-python（默认） | 86 | 65 上游 + 17 收纳 + 4 自有 |
| full | 151 | 129 上游 + 18 收纳 + 4 自有 |
| lite | 43 | 39 上游 + 0 收纳 + 4 自有 |

`docs/CATALOG.md` 的 82/146/39 是「上游 + 收纳、不含自有」，与 README 的口径一致。

## Windows 上的坑

- `core.autocrlf=true` 会把 checkout 的字节写成 CRLF，`absorbed/` 的摘要随即与干净 clone
  对不上。`absorbed/**` 与 `*.ts/*.js/*.mjs/*.sh` 已进 `.gitattributes` 的 `eol=lf`。
- `python tools/xxx.py | head` 会在管道关闭时抛 `OSError 22`，属假故障，别照着改代码。
- `apply_selection.py` 单独跑，不要接管道；否则 `manifest/applied.json` 可能不落盘。
- `am render` 写中文名页面会 exit 9（页面其实已生成），用 `-o` 给 ASCII 输出名绕过。

## 发布后要验的

```bash
omp skill list | grep forge-router     # 描述是中文且带触发词
git status --porcelain                 # 空
gh run list --limit 1                  # CI success
```

skill 是每轮注入的提示行，改完描述立即生效；skill 正文与 agent 变更要新会话或重载插件。

## 结构上的硬约束

- `pool/` 只由 `tools/sync_upstream.py` 改写，必须与上游 pin 逐字节一致。
- `own/skills/` 是 fork 自有资产，无条件进所有 profile，无法按 profile 裁剪。
- 第三方 skill 走 `absorbed/`（见 ADR-0010），按来源 pin 到 commit，手动 bump。
- skill 提示行描述走 `manifest/skill_descriptions.zh.json`（见 ADR-0011），物化时写进运行树。
- 运行名统一 `forge-` 前缀；上游名只活在 `pool/` 与 manifest 里。
