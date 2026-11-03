---
name: forge-ci-triage
description: 定位本插件仓库的 CI（sync-upstream workflow）失败：日志按 profile 分组读、本地三 profile 复现、门禁分工与部署副本同步
---

# 本插件 CI 失败定位

CI workflow：`.github/workflows/sync-upstream.yml`（job：同步上游 ECC 并逐 profile 跑门禁）。
仓库与本地工作区同源，远端是 `meisijiya/omp-skill-forge`。

## 1. 先信日志，不信汇总行

profile 循环里的 `failed` 标志是**累积**的：一旦某个 profile 挂掉，后续每个 profile 都会打印
`profile <X> failed a gate (apply_selection=0, check_adapt=0, check_refs=0)`，
报错名义上指向**最后一个** profile，实际失败的是最早出错的那个。

按 profile 分组读日志：

```bash
gh run view <run-id> --log 2>&1 | grep -E "violations:|dangling references|profile:|result: consistent"
```

- `violations: N`（check_adapt 输出）→ 看它前面最近的 `profile: <name>` 行。
- `dangling references: N`（check_refs 输出）→ 同上；`profile-cropped references in the fork's
  own catalog: N` 是 notice，不是缺陷。
- `result: consistent (4 checks passed)` → check_upstream_pin 通过。

## 2. 本地复现（CI 只跑 committed profile，本地必须跑全）

committed profile 是 `manifest/selection.json` 的 `active_profile`（通常 java-python）。
改名类改动必须三个 profile 都跑：

```bash
for p in full java-python lite; do
  python -c "import json,io;s=json.load(open('manifest/selection.json',encoding='utf-8'));s['active_profile']='$p';open('manifest/selection.json','w',encoding='utf-8').write(json.dumps(s,indent=2,ensure_ascii=False)+'\n')"
  python tools/apply_selection.py && python tools/check_adapt.py && python tools/check_refs.py
done
git checkout -- manifest/selection.json
python tools/apply_selection.py && python tools/build_catalog.py
```

退出码全 0 才算通过；`check_refs` 打印 `dangling references: 0` 但退出码非 0 也要当失败看。

## 3. 门禁分工

| 工具 | 管什么 | 典型失败 |
|---|---|---|
| `tools/check_refs.py` | 悬空引用（defect）vs 裁剪引用（notice） | `skill:// reference, no such skill` / `named in an asset context, but no such asset in the active profile` |
| `tools/check_adapt.py` | INV-01..INV-15 适配不变式 | INV-14：斜杠形式的命令引用必须指向本树提供的命令（本 tree 不发布命令，故运行树里不该出现斜杠命令引用）；INV-07/INV-10：frontmatter `name` == 目录名/文件名 |
| `tools/check_upstream_pin.py` | pin、镜像、池摘要、NOTICE.md 引用 commit 四者一致 | `NOTICE.md cites upstream commit <sha>, but the pin is <commit>` |
| `tools/check_absorbed.py` | 收纳池的 pin、摘要、生成物、许可、换行符与残留文本 | 收纳副本里残留别的 harness 的项目文件写法；或生成物与输入不一致 |
| `tools/check_zh_descriptions.py` | 每条 skill/agent 的中文触发描述齐且合规 | 缺条目（新增 skill/agent 后）、超 45 token、出现冒号 |
| `tools/upstream_versions.py check --offline` | 逐资产台账覆盖与形状 | 缺资产条目（新增/删除 skill 后要重跑 `record`） |
| `tools/check_plugin_isolation.py --toggle-test` | 插件启停可见性 | 需先 `python tools/deploy.py`，否则报 `installed plugin root differs from the repo tree` |

引用判定只有 `tools/refscan.py` 一份实现（ADR-0002）：改引用形态就改它，不要在别的工具里另写正则。

## 4. 提交与推送

- 提交前确认 `git status --porcelain` 为空，且 `python tools/build_catalog.py` 后 `docs/CATALOG.md` 无 diff。
- 推送后看 CI run 结论；`gh run list --limit 3`。
- deploy 到 `~/.omp/agent/local/omp-skill-forge` 与发布属于需用户批准的动作。
