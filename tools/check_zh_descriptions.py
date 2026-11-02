#!/usr/bin/env python
"""Gate: every skill and agent this fork ships must have a Chinese trigger description.

    python tools/check_zh_descriptions.py [--json]

Chinese prompts only match Chinese descriptions.  The upstream ECC snapshot
must stay byte-identical to its pin (tools/check_upstream_pin.py), so the
Chinese descriptions live in manifest/skill_descriptions.zh.json and are
written into the runtime tree by tools/apply_selection.py.  This gate
proves three things offline:

  1. coverage -- every skill of every profile and every agent of every
     profile has a Chinese description, and the table names no asset that
     does not exist;
  2. style -- each description obeys the writing rules below;
  3. the fork's own skills carry a Chinese description in their own file.

Both tables live in manifest/: skill_descriptions.zh.json and
agent_descriptions.zh.json.  A missing table is reported as a missing table
and exits non-zero rather than passing silently.

Writing rules (one line per skill, shown in the omp prompt line):
  * the line costs at most 45 tokens: one Chinese character counts as one
    token, every other character as a third of a token, which is how the
    prompt line is paid for;
  * at most one enumeration comma, so at most two items share one clause;
  * no colon, no em dash, and none of the phrases the tone rules reject:
    不是…而是, 并非…而是, 说白了, 首先, 其次, 赋能, 闭环, 抓手, 落地;
  * it says what the skill does and when to reach for it, in Chinese.

Exit codes: 0 clean, 1 defects, 2 unreadable input.
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "manifest", "skill_descriptions.zh.json")
AGENT_TABLE = os.path.join(ROOT, "manifest", "agent_descriptions.zh.json")

MAX_COST = 45.0
MIN_COST = 12.0
FORBIDDEN = ["说白了", "首先", "其次", "赋能", "闭环", "抓手", "落地"]
# the fork must not point at another harness (INV-02, INV-03, INV-15)
HARNESS = ["CLAUDE.md", ".claude/", "Claude Code", "PreToolUse", "AskUserQuestion"]
# 翻案腔: 立一个读者没有的误解再推翻它。单独的「不是给 X 用的」不算翻案腔。
CONTRAST = re.compile(r"不是[^。；]{0,20}而是|并非[^。；]{0,20}而是")
CJK = re.compile(r"[\u4e00-\u9fff]")
DUNHAO = "、"


def line_cost(text):
    """Prompt-line cost of a description: one token per Chinese character."""
    cjk = len(CJK.findall(text))
    return cjk + (len(text) - cjk) / 3.5


def defect(findings, kind, where, detail):
    findings.append({"kind": kind, "file": where, "detail": detail})


def load_table(findings):
    try:
        with open(TABLE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read {TABLE}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"{TABLE} is not a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return data


def load_agent_table(findings):
    """Load the agent description table; report 缺表 instead of crashing."""
    try:
        with open(AGENT_TABLE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        defect(findings, "coverage", "agents", "缺表: manifest/agent_descriptions.zh.json")
        return None
    except (OSError, ValueError) as exc:
        print(f"cannot read {AGENT_TABLE}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"{AGENT_TABLE} is not a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return data


def declared_skills():
    """Every skill name the repository can materialize."""
    names = set()
    groups = json.load(open(os.path.join(ROOT, "manifest", "groups.json"),
                            encoding="utf-8"))["skills"]
    for code in groups:
        names.update(groups[code]["members"])
    absorbed = json.load(open(os.path.join(ROOT, "manifest", "absorbed.json"),
                              encoding="utf-8"))["skills"]
    names.update(absorbed)
    return names


def declared_agents():
    """Every agent name the repository can materialize."""
    names = set()
    groups = json.load(open(os.path.join(ROOT, "manifest", "groups.json"),
                            encoding="utf-8"))["agents"]
    for code in groups:
        names.update(groups[code]["members"])
    return names


def check_style(findings, name, text, owner):
    # the same writing rules govern skills and agents, but the defect path has
    # to point at the table the offender came from, else troubleshooting opens
    # the wrong manifest
    where = f"{owner}/{name}"
    if not CJK.search(text):
        defect(findings, "coverage", where, "description has no Chinese characters")
    cost = line_cost(text)
    if cost > MAX_COST:
        defect(findings, "style", where,
               f"{cost:.1f} tokens, limit is {MAX_COST}")
    if cost < MIN_COST:
        defect(findings, "style", where,
               f"{cost:.1f} tokens, minimum is {MIN_COST}")
    if ":" in text or "：" in text:
        defect(findings, "style", where, "contains a colon")
    if "—" in text or "--" in text:
        defect(findings, "style", where, "contains a dash")
    if text.count(DUNHAO) > 1:
        defect(findings, "style", where, "more than one enumeration comma")
    for word in FORBIDDEN:
        if word in text:
            defect(findings, "style", where, f"contains rejected wording {word!r}")
    if CONTRAST.search(text):
        defect(findings, "style", where, "uses the 不是…而是 contrast")
    for word in HARNESS:
        if word in text:
            defect(findings, "style", where, f"names another harness {word!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    findings = []
    table = load_table(findings)
    known = declared_skills()

    for name in sorted(known - set(table)):
        defect(findings, "coverage", f"skills/{name}",
               "no Chinese description in manifest/skill_descriptions.zh.json")
    for name in sorted(set(table) - known):
        defect(findings, "coverage", f"skills/{name}",
               "table names a skill the repository does not ship")

    for name, text in sorted(table.items()):
        if not isinstance(text, str):
            defect(findings, "coverage", f"skills/{name}", "description is not text")
            continue
        check_style(findings, name, text, "skills")

    agent_table = load_agent_table(findings)
    if agent_table is not None:
        agent_known = declared_agents()
        for name in sorted(agent_known - set(agent_table)):
            defect(findings, "coverage", f"agents/{name}",
                   "no Chinese description in manifest/agent_descriptions.zh.json")
        for name in sorted(set(agent_table) - agent_known):
            defect(findings, "coverage", f"agents/{name}",
                   "table names an agent the repository does not ship")
        for name, text in sorted(agent_table.items()):
            if not isinstance(text, str):
                defect(findings, "coverage", f"agents/{name}", "description is not text")
                continue
            check_style(findings, name, text, "agents")

    own = os.path.join(ROOT, "own", "skills")
    if os.path.isdir(own):
        for name in sorted(os.listdir(own)):
            path = os.path.join(own, name, "SKILL.md")
            if not os.path.isfile(path):
                continue
            head = open(path, encoding="utf-8").read().split("---", 2)
            desc = ""
            for line in (head[1] if len(head) > 2 else "").splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
            if not CJK.search(desc):
                defect(findings, "coverage", f"own/skills/{name}",
                       "the fork's own skill needs a Chinese description")

    if args.json:
        print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
    else:
        if not findings:
            agents = "" if agent_table is None else " + %d agents" % len(agent_table)
            print("chinese descriptions: complete (%d skills%s)" % (len(table), agents))
        for f in findings:
            print(f"{f['kind']}: {f['file']}: {f['detail']}")
        print("\n%d defect(s)" % len(findings))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
