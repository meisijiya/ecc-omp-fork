#!/usr/bin/env python
"""Generate docs/CATALOG.md from manifest/groups.json + the materialized tree.

The catalog lists every upstream asset with its group, whether it is currently
enabled, and which profile enables it. It is generated, not hand-maintained, so
it cannot drift from the profile definitions.

Inputs
  manifest/groups.json          group -> member classification (all three kinds)
  manifest/selection.json       active profile pointer + extra items
  manifest/profiles/<p>.json    the profile's group/exclude/include choices

The profile set is indexed by FILE NAME, because that is the key
apply_selection.py resolves `selection.json:active_profile` with. The JSON body
carries a second, redundant identity field ("profile"); if the two disagree the
catalog would advertise a profile name that apply_selection never loads, so
that mismatch is a hard error instead of a silent preference for one of them.

    python tools/build_catalog.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refscan  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ("skills", "commands", "agents")
INCLUDE_MARK = "+"
EXTRA_MARK = "extra"
ABSORBED_MARK = "收纳"


def load(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def load_profiles():
    """Index profile definitions by file name -> profile dict."""
    pdir = os.path.join(ROOT, "manifest", "profiles")
    if not os.path.isdir(pdir):
        raise SystemExit(f"missing profile directory: {pdir}")
    profiles = {}
    for fn in sorted(os.listdir(pdir)):
        if not fn.endswith(".json"):
            continue
        name = fn[: -len(".json")]
        p = load("manifest", "profiles", fn)
        declared = p.get("profile")
        if declared != name:
            raise SystemExit(
                f"profile identity mismatch: manifest/profiles/{fn} declares "
                f"{declared!r} but apply_selection.py resolves it as {name!r}"
            )
        profiles[name] = p
    return profiles


def load_extra(selection):
    """Return {kind: [name]} for the extra items selection.json appends."""
    extra = selection.get("extra") or {}
    unknown = set(extra) - set(KINDS)
    if unknown:
        raise SystemExit(
            f"manifest/selection.json extra has unknown keys {sorted(unknown)};"
            f" allowed: {sorted(KINDS)}"
        )
    return {kind: list(extra.get(kind, [])) for kind in KINDS}


def profile_members(groups, profile, extra=None):
    """Return {kind: {member: source}} for the assets a profile enables.

    `source` is the group code for group members, "+" for include-only entries
    and "extra" for entries appended through selection.json's `extra` block.
    """
    out = {k: {} for k in KINDS}
    for name in profile.get("absorbed", ()):
        out["skills"][name] = ABSORBED_MARK
    for kind in KINDS:
        sel = profile.get(kind, {})
        exclude = set(sel.get("exclude", []))
        for code in sel.get("groups", []):
            if code not in groups.get(kind, {}):
                raise SystemExit(
                    f"unknown group {code!r} for {kind}: manifest/groups.json "
                    f"defines {sorted(groups.get(kind, {}))}"
                )
            for name in groups[kind][code]["members"]:
                if name not in exclude and name not in out[kind]:
                    out[kind][name] = code
        for name in sel.get("include", []):
            out[kind].setdefault(name, INCLUDE_MARK)
        for name in (extra or {}).get(kind, []):
            out[kind].setdefault(name, EXTRA_MARK)
    return out


def build_origin(groups, members_by_profile, extras):
    """Return {kind: [(name, group_cell)]} in a stable display order.

    Every asset a profile can select gets a row: group members, include-only
    assets that belong to no group, and assets appended through `extra`.
    """
    origin = {kind: {} for kind in KINDS}
    order = {kind: [] for kind in KINDS}
    for kind in KINDS:
        for code, g in groups.get(kind, {}).items():
            for name in g.get("members", []):
                if name not in origin[kind]:
                    origin[kind][name] = code
                    order[kind].append(name)
        for members in members_by_profile:
            for name, src in members[kind].items():
                if src in (INCLUDE_MARK, ABSORBED_MARK) and name not in origin[kind]:
                    origin[kind][name] = src
                    order[kind].append(name)
        for name in extras[kind]:
            if name not in origin[kind]:
                origin[kind][name] = EXTRA_MARK
                order[kind].append(name)
    return {kind: [(n, origin[kind][n]) for n in order[kind]] for kind in KINDS}


def materialized():
    """Return {kind: set(name)} for what is actually on disk right now."""
    out = {}
    for kind in KINDS:
        d = os.path.join(ROOT, kind)
        if not os.path.isdir(d):
            out[kind] = set()
            continue
        if kind == "skills":
            out[kind] = {
                n for n in os.listdir(d)
                if os.path.isdir(os.path.join(d, n))
            }
        else:
            out[kind] = {
                os.path.splitext(n)[0] for n in os.listdir(d)
                if n.endswith(".md")
            }
    return out


def main():
    groups = load("manifest", "groups.json")
    selection = load("manifest", "selection.json")
    active = selection.get("active_profile")
    if not active:
        raise SystemExit("manifest/selection.json has no 'active_profile' field")
    extras = load_extra(selection)
    profiles = load_profiles()
    if active not in profiles:
        raise SystemExit(
            f"unknown active profile {active!r}: "
            f"manifest/profiles/{active}.json not found"
        )

    members_by_profile = {}
    for name, p in profiles.items():
        extra = extras if name == active else None
        members_by_profile[name] = profile_members(groups, p, extra)

    absorbed_skills = load("manifest", "absorbed.json").get("skills", {})
    unknown_absorbed = sorted(
        {n for p in profiles.values() for n in p.get("absorbed", ())}
        - set(absorbed_skills))
    if unknown_absorbed:
        raise SystemExit(
            f"profiles select absorbed skills manifest/absorbed.json does not"
            f" declare: {unknown_absorbed}")
    enabled = materialized()
    rows = build_origin(groups, list(members_by_profile.values()), extras)

    lines = [
        "# ECC-OMP-Fork 资产目录",
        "",
        "> 由 `tools/build_catalog.py` 生成，勿手改。",
        "> 上游：[affaan-m/ECC](https://github.com/affaan-m/ECC)（MIT）。",
        "",
        f"当前生效 profile：**{active}**。",
        "",
        "| profile | 说明 | skills | commands | agents |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in sorted(profiles):
        p = profiles[name]
        counts = [str(len(members_by_profile[name][kind])) for kind in KINDS]
        lines.append(
            f"| `{name}` | {p.get('description','')} | " + " | ".join(counts) + " |"
        )

    lines += [
        "",
        "> 表里的**运行名**是本 fork 物化后实际使用的名字：上游名统一加 "
        f"`{refscan.RUNTIME_PREFIX}` 前缀（skill / command / agent）。",
        "> 「上游名」是 affaan-m/ECC 里的名称，用于回溯上游来源；组列写「收纳」的资产"
        "来自 fork 之外的仓库，经改写后随本 fork 发布（ADR-0010，来源见 "
        "`manifest/absorbed.json`），它们的「上游名」一列是来源仓库里的名字，不是 ECC 名。",
    ]

    for kind in KINDS:
        lines += ["", f"## {kind.capitalize()}", ""]
        if not any(members_by_profile[p][kind] for p in profiles):
            lines.append(
                "本 fork 不发布这类资产。上游快照仍保留在 `pool/` 里（供回溯与日后恢复），"
                "但不物化、不发布。"
            )
            lines.append("")
            continue
        lines.append("| 组 | 名称（运行名） | 上游名 | 生效 profile |")
        lines.append("| --- | --- | --- | --- |")
        for name, cell in rows[kind]:
            on = [
                pname for pname in sorted(profiles)
                if name in members_by_profile[pname][kind]
            ]
            runtime = refscan.runtime_name(name)
            mark = "✅" if runtime in enabled[kind] else "⬜"
            tag = " (extra)" if name in extras[kind] else ""
            lines.append(
                f"| {cell} | {mark} `{runtime}`{tag} | `{name}` | "
                f"{', '.join(on) or '—'} |"
            )

    own_skills = os.path.join(ROOT, "own", "skills")
    own_purpose = {
        "forge-router": "选路表：任务 → skill / agent 组合",
        "forge-release-management": "发布：tag、changelog、分级发布与回滚",
        "forge-observability": "可观测性：日志 / 指标 / 追踪、SLO、告警",
        "forge-incident-response": "事故响应：定级、止血、复盘",
    }
    found = sorted(os.listdir(own_skills)) if os.path.isdir(own_skills) else []
    if found != sorted(own_purpose):
        raise SystemExit(
            f"own/skills holds {found}, but build_catalog knows {sorted(own_purpose)};"
            " add the new skill here and to own_purpose")
    lines += [
        "",
        "## fork 自有资产",
        "",
    ]
    lines += [f"- skill：`{n}`（{own_purpose[n]}）" for n in found]
    lines += [
        "- rules：`omp-tooling` `omp-delegation` `fork-workflow` `fork-verification` `fork-coding-style`",
        "",
    ]

    out = os.path.join(ROOT, "docs", "CATALOG.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("wrote", out)


if __name__ == "__main__":
    main()
