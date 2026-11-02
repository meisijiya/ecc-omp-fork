#!/usr/bin/env python
"""逐条上游版本台账：记录每个上游资产在其 pin 提交下的 git tree oid，
并对照远端 HEAD 检测上游漂移。

子命令:
  record  --source <slug>   用当前 pin 的提交重算台账
  check   --source <slug>   对比远端 HEAD 与台账，报告漂移
  check   --offline         不联网，只校验台账形状与资产覆盖（CI 跑这条）
  show                      打印台账摘要

退出码: 0 无漂移 / 1 发现漂移 / 2 用法或网络错误。

实现约定:
  - 缓存目录 .upstream-cache/<slug>（gitignore，不入库）。
  - ECC 体积大，用 --filter=blob:none --depth 1 浅取；第三方仓普通浅克隆。
  - 所有 git 调用加 -c http.version=HTTP/1.1（本机网络 HTTP/2 中途断流）。
  - 只读：不改工作树、不 push、不写别的仓库；网络失败给可读报错。
  - 只依赖标准库，Python 3.10+。
  - 台账 tree oid 可直接用 `git rev-parse <commit>:<path>` 验证。
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_ROOT = os.path.join(ROOT, ".upstream-cache")
LEDGER_PATH = os.path.join(ROOT, "manifest", "asset_versions.json")

UPSTREAM_MANIFEST = os.path.join(ROOT, "manifest", "upstream.json")
GROUPS_MANIFEST = os.path.join(ROOT, "manifest", "groups.json")
ABSORBED_MANIFEST = os.path.join(ROOT, "manifest", "absorbed.json")

GIT_HTTP = ["-c", "http.version=HTTP/1.1"]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

LEDGER_VERSION = 1


class LedgerError(Exception):
    """可读错误，向上打印后以退出码 2 结束。"""


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """UTF-8、LF、trailing newline 的原子写盘。"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def git(args, cwd=None):
    """跑一个 git 调用，返回 CompletedProcess；不抛异常。"""
    cmd = ["git"] + GIT_HTTP
    if cwd is not None:
        cmd += ["-C", cwd]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def git_checked(args, cwd=None, what="git"):
    r = git(args, cwd=cwd)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        raise LedgerError(f"{what} 失败: {detail}")
    return r


# --------------------------------------------------------------------------
# 来源与资产定义（读 manifest，不含网络）
# --------------------------------------------------------------------------

def ecc_assets():
    """ECC 上游资产：groups.json 的 skills 成员 + agents 成员。

    返回 {name: {"path": 上游仓库内路径, "kind": "skill"|"agent"}}。
    """
    groups = read_json(GROUPS_MANIFEST)
    assets = {}
    for group in groups.get("skills", {}).values():
        for name in group.get("members", []):
            assets[name] = {"path": f"pi/core/skills/{name}", "kind": "skill"}
    for group in groups.get("agents", {}).values():
        for name in group.get("members", []):
            assets[name] = {"path": f"agents/{name}.md", "kind": "agent"}
    return assets


def absorbed_assets(slug):
    """某个第三方来源的资产：absorbed.json 的 skills 条目（不含 bundle）。"""
    ab = read_json(ABSORBED_MANIFEST)
    assets = {}
    for name, entry in ab.get("skills", {}).items():
        if entry.get("source") != slug:
            continue
        assets[name] = {"path": entry["path"], "kind": "skill"}
    return assets


def all_sources():
    """所有来源定义: {slug: {repo, commit, ecc, assets}}。"""
    sources = {}
    up = read_json(UPSTREAM_MANIFEST)
    sources["ecc"] = {
        "repo": up["repo"],
        "commit": up["commit"],
        "ecc": True,
        "assets": ecc_assets(),
    }
    ab = read_json(ABSORBED_MANIFEST)
    for slug, meta in ab.get("sources", {}).items():
        sources[slug] = {
            "repo": meta["repo"],
            "commit": meta["commit"],
            "ecc": False,
            "assets": absorbed_assets(slug),
        }
    return sources


def pick_sources(sources, source):
    if source is None:
        return sources
    if source not in sources:
        raise LedgerError(f"未知来源 {source!r}；可用: {', '.join(sources)}")
    return {source: sources[source]}


def cache_dir(slug):
    return os.path.join(CACHE_ROOT, slug)


# --------------------------------------------------------------------------
# 缓存克隆管理（只读，不 checkout 工作树）
# --------------------------------------------------------------------------

def commit_present(repo, sha):
    return git(["cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo).returncode == 0




def fetch_commit(path, source, sha, what):
    cmd = ["fetch", "--depth", "1"]
    if source["ecc"]:
        cmd.append("--filter=blob:none")
    cmd += ["origin", sha]
    r = git(cmd, cwd=path)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        raise LedgerError(f"拉取 {what} {sha[:12]} 失败: {detail}")
    git_checked(["config", "http.version", "HTTP/1.1"], cwd=path,
                what=f"config {os.path.basename(path)}")

def ensure_clone(source):
    """确保缓存克隆存在且包含 source["commit"]；返回克隆路径。"""
    slug = source["slug"]
    path = cache_dir(slug)
    if not os.path.isdir(os.path.join(path, ".git")):
        os.makedirs(CACHE_ROOT, exist_ok=True)
        cmd = ["clone", "--depth", "1"]
        if source["ecc"]:
            cmd.append("--filter=blob:none")
        cmd += [source["repo"], path]
        git_checked(cmd, what=f"clone {slug}")
        git_checked(["config", "http.version", "HTTP/1.1"], cwd=path,
                    what=f"config {slug}")
    if not commit_present(path, source["commit"]):
        fetch_commit(path, source, source["commit"], what=f"{slug} pin 提交")
    return path

def tree_oid(repo, commit, path):
    """路径在 commit 下的 git 对象 id（目录=tree，文件=blob）。缺失返回 None。"""
    r = git(["rev-parse", f"{commit}:{path}"], cwd=repo)
    if r.returncode != 0:
        return None
    oid = r.stdout.strip()
    return oid if oid else None


def version_file(asset):
    if asset["kind"] == "agent":
        return asset["path"]
    return asset["path"] + "/SKILL.md"


def read_version(repo, commit, asset):
    """读上游资产 frontmatter 的 version: 值；没有就返回 None。"""
    vf = version_file(asset)
    r = git(["show", f"{commit}:{vf}"], cwd=repo)
    if r.returncode != 0:
        return None
    text = r.stdout
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fm = text[3:end]
    m = re.search(r"(?m)^version:\s*(.+?)\s*$", fm)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def remote_head(repo_url):
    r = git(["ls-remote", repo_url, "HEAD"])
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        raise LedgerError(f"取远端 HEAD 失败 ({repo_url}): {detail}")
    out = r.stdout.strip()
    if not out:
        raise LedgerError(f"远端 {repo_url} 的 HEAD 为空")
    sha = out.split()[0]
    if not SHA_RE.match(sha):
        raise LedgerError(f"远端 {repo_url} 返回了非常规 HEAD: {sha!r}")
    return sha


# --------------------------------------------------------------------------
# 台账读写
# --------------------------------------------------------------------------

def load_ledger():
    if not os.path.isfile(LEDGER_PATH):
        raise LedgerError(f"台账不存在: {LEDGER_PATH}；先跑 record")
    return read_json(LEDGER_PATH)


def new_ledger():
    return {"version": LEDGER_VERSION, "sources": {}}


# --------------------------------------------------------------------------
# record
# --------------------------------------------------------------------------

def cmd_record(source):
    sources = pick_sources(all_sources(), source)
    ledger = load_ledger() if os.path.isfile(LEDGER_PATH) else new_ledger()
    # 只动本次指定的来源，其余保留。
    if "sources" not in ledger:
        ledger = new_ledger()
    for slug, src in sources.items():
        src["slug"] = slug
        clone = ensure_clone(src)
        assets = {}
        for name, asset in sorted(src["assets"].items()):
            oid = tree_oid(clone, src["commit"], asset["path"])
            if oid is None:
                print(f"  ! {slug}/{name}: 上游 pin 下不存在 {asset['path']}")
            assets[name] = {
                "path": asset["path"],
                "tree": oid,
                "version": read_version(clone, src["commit"], asset),
            }
        ledger["sources"][slug] = {
            "repo": src["repo"],
            "commit": src["commit"],
            "assets": assets,
        }
        n = len(assets)
        miss = sum(1 for a in assets.values() if a["tree"] is None)
        print(f"[{slug}] 记录 {n} 个资产 @ {src['commit'][:12]}"
              + (f"（{miss} 个在 pin 下缺失）" if miss else ""))
    write_json(LEDGER_PATH, ledger)
    print(f"写入 {LEDGER_PATH}")


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def cmd_check(source):
    sources = pick_sources(all_sources(), source)
    ledger = load_ledger()
    if "sources" not in ledger:
        raise LedgerError("台账格式无效: 缺 sources")
    drift_found = False
    for slug, src in sources.items():
        src["slug"] = slug
        rec = ledger["sources"].get(slug)
        if rec is None:
            print(f"[{slug}] 台账无该来源记录，跳过")
            continue
        head = remote_head(src["repo"])
        clone = ensure_clone({"repo": src["repo"], "commit": head,
                              "ecc": src["ecc"], "slug": slug})
        cur_assets = src["assets"]  # 当前下游资产定义
        rec_assets = rec.get("assets", {})
        changed, new, removed_down, upstream_gone, upstream_restored = (
            [], [], [], [], []
        )
        for name, asset in sorted(rec_assets.items()):
            if name not in cur_assets:
                removed_down.append((name, asset["path"]))
                continue
            head_oid = tree_oid(clone, head, asset["path"])
            rec_oid = asset.get("tree")
            if rec_oid is None and head_oid is None:
                # 合成资产（如 bundle）：pin 与 HEAD 下都不存在，非漂移。
                continue
            if head_oid is None:
                upstream_gone.append((name, asset["path"], rec_oid))
            elif head_oid != rec_oid:
                changed.append((name, asset["path"], rec_oid, head_oid))
        for name in sorted(set(cur_assets) - set(rec_assets)):
            new.append((name, cur_assets[name]["path"]))

        drift_found = drift_found or bool(changed or new or removed_down
                                          or upstream_gone)
        if not (changed or new or removed_down or upstream_gone):
            print(f"[{slug}] 无漂移 @ HEAD {head[:12]} "
                  f"（{len(rec_assets)} 个资产）")
            continue
        print(f"[{slug}] 发现漂移 @ HEAD {head[:12]}:")
        for name, path, old, new_oid in changed:
            print(f"  上游变了  {name} ({path})")
            print(f"    {old[:12]} -> {new_oid[:12]}")
        for name, path, _ in upstream_gone:
            print(f"  上游已删  {name} ({path})")
        for name, path in new:
            print(f"  新增下游  {name} ({path})")
        for name, path in removed_down:
            print(f"  下游已删  {name} ({path})")
    return 1 if drift_found else 0


# --------------------------------------------------------------------------
# show
# --------------------------------------------------------------------------

def cmd_check_offline():
    """不联网：校验台账形状与覆盖。

    每个 manifest 当前来源的每个资产在台账里有条目；台账里没有
    已删除（清单里不再存在）的资产条目；每个 tree 是 40 位十六进制
    或 null。形状错误退出 1，否则 0。离线模式下不比对内容漂移。
    """
    ledger = load_ledger()
    sources = ledger.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise LedgerError("台账格式无效: sources 缺失或非空")
    cur = all_sources()
    problems = []
    for slug, src in sorted(cur.items()):
        rec = sources.get(slug)
        if not isinstance(rec, dict) or "assets" not in rec:
            problems.append(f"[{slug}] 台账缺来源记录")
            continue
        rec_assets = rec["assets"] or {}
        for name, asset in sorted(src["assets"].items()):
            if name not in rec_assets:
                problems.append(f"[{slug}] 缺资产条目 {name} ({asset['path']})")
                continue
            tree = rec_assets[name].get("tree")
            if tree is not None and not SHA_RE.match(tree):
                problems.append(f"[{slug}] {name} 的 tree 不是 40 位十六进制或 null: {tree!r}")
        for name in sorted(set(rec_assets) - set(src["assets"])):
            problems.append(f"[{slug}] 台账含已删除资产 {name}")
    if problems:
        print("台账形状/覆盖校验失败:")
        for p in problems:
            print(f"  {p}")
        return 1
    total = sum(len(v.get("assets", {})) for v in sources.values())
    print(f"台账形状/覆盖校验通过：{len(sources)} 个来源，{total} 个资产条目")
    return 0


 # --------------------------------------------------------------------------
 # show
 # --------------------------------------------------------------------------
def cmd_show():
    ledger = load_ledger()
    sources = ledger.get("sources", {})
    if not sources:
        print("台账为空")
        return
    print(f"asset_versions.json  version={ledger.get('version')}")
    total = 0
    for slug, rec in sources.items():
        assets = rec.get("assets", {}) or {}
        total += len(assets)
        versions = {a.get("version") for a in assets.values()
                    if a.get("version") is not None}
        ver = f", 声明版本 {sorted(versions)}" if versions else ""
        print(f"[{slug}] {rec.get('repo')} @ {rec.get('commit', '')[:12]}"
              f"，{len(assets)} 个资产{ver}")
        for name, a in sorted(assets.items()):
            tree = a.get("tree")
            tree_disp = tree[:12] if tree else "-"
            v = f", version={a.get('version')}" if a.get("version") else ""
            print(f"    {name:36s} {tree_disp}{v}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="逐条上游版本台账：记录资产 tree oid 并检测上游漂移。",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_record = sub.add_parser("record", help="用当前 pin 提交重算台账")
    p_record.add_argument("--source", default=None,
                          help="只处理该来源（缺省全部）")

    p_check = sub.add_parser("check", help="对比远端 HEAD 与台账")
    p_check.add_argument("--source", default=None,
                         help="只检查该来源（缺省全部）")
    p_check.add_argument("--offline", action="store_true",
                         help="不联网，只校验台账形状与覆盖")

    sub.add_parser("show", help="打印台账摘要")

    args = ap.parse_args()
    try:
        if args.cmd == "record":
            cmd_record(args.source)
            return 0
        if args.cmd == "check":
            return cmd_check_offline() if args.offline else cmd_check(args.source)
        if args.cmd == "show":
            cmd_show()
            return 0
        ap.error(f"未知子命令 {args.cmd}")
    except LedgerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
