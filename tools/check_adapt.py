#!/usr/bin/env python
"""Gate: the materialized tree must stay free of Claude-harness references.

The fork rewrites upstream ECC assets for omp. Every rewrite is a promise
that the shipped text no longer points at the Claude harness: no
`CLAUDE.md`, no `~/.claude/` directory, no `claude` CLI call, no Claude tool
name, no "Claude Code" wording. This gate is the detection side of that
promise -- it reports what is left, it never rewrites anything.

The invariants are shared with the repair side (tools/apply_selection.py and
own/patches/), so both sides agree on what a violation is. INV-01 .. INV-15:

  INV-01  no `model:` key in any frontmatter block
  INV-02  no `CLAUDE.md` file reference
  INV-03  no `.claude/` directory reference
  INV-04  no `claude` CLI invocation
  INV-05  no Claude tool name (bare `AskUserQuestion` .., backticked
          `Read` / `Edit` / `Write` / `Grep` / `Glob` / `Bash` /
          `MultiEdit`; a bare backticked `Task` is the C# type and is
          left alone)
  INV-06  a skill frontmatter has a non-empty `name` and `description`
  INV-07  a skill's `name` equals its directory name
  INV-08  every skill directory holds exactly one `SKILL.md`, and no
          `SKILL.md` sits deeper than `skills/<skill>/SKILL.md`
  INV-09  an agent frontmatter has a non-empty `name` and `description`, and
          the agent has a body (omp reads the body as the system prompt)
  INV-10  an agent's `name` equals its file name and is not a reserved name
  INV-11  an agent's `tools:` list names no Claude tool
  INV-12  a rule has a non-empty `description` or `alwaysApply: true`
  INV-13  a command has a non-empty `description`
  INV-14  every `/command` reference names a command this tree ships
  INV-15  no "Claude Code" wording

Three exemptions are built in and cannot be switched off:

  * `rules/omp-tooling.md` is the fork's own mapping table. It has to name
    "Claude Code" and the Claude tool names to do its job, so INV-05 and
    INV-15 do not apply to it.
  * The Anthropic products are not the harness. `Claude API`,
    `Claude Desktop`, `claude-haiku`, the ECC CLI parameter `claude-project`
    and the `CLAUDE_MAP.md` document role are never reported by any rule.
  * The fork's own catalog files (own/skills/, own/rules/ and their copies
    in the runtime tree) describe the whole fork, so a `/command` that this
    profile cropped is expected there. INV-14 still applies to them when the
    command does not exist upstream at all.

Usage
  python tools/check_adapt.py                 # scan the repository tree
  python tools/check_adapt.py --tree <dir>    # scan another tree
  python tools/check_adapt.py --json          # machine readable report

Exit codes
  0  no violation
  1  violations found
  2  the tree could not be inspected / usage error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mdmeta  # noqa: E402
import refscan  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCAN_DIRS = ("skills", "commands", "agents", "rules")
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv"}

# --- the invariants --------------------------------------------------------

INVARIANTS = [
    ("INV-01", "no `model:` key in any frontmatter block"),
    ("INV-02", "no `CLAUDE.md` file reference"),
    ("INV-03", "no `.claude/` directory reference"),
    ("INV-04", "no `claude` CLI invocation"),
    ("INV-05", "no Claude tool name"),
    ("INV-06", "a skill frontmatter has `name` and `description`"),
    ("INV-07", "a skill's `name` equals its directory name"),
    ("INV-08", "every skill directory holds exactly one `SKILL.md`"),
    ("INV-09", "an agent has `name`, `description` and a body"),
    ("INV-10", "an agent's `name` equals its file name"),
    ("INV-11", "an agent's `tools:` names no Claude tool"),
    ("INV-12", "a rule has a `description` or `alwaysApply: true`"),
    ("INV-13", "a command has a `description`"),
    ("INV-14", "every `/command` reference names a shipped command"),
    ("INV-15", "no \"Claude Code\" wording"),
]

# Files that are allowed to name the Claude harness: the fork's own table
# of the upstream tool names.
EXEMPT_FILES = {"rules/omp-tooling.md"}
EXEMPT_INVARIANTS = {"INV-05", "INV-15"}

# Anthropic products are not the harness and are never reported.
WHITELIST_TOKENS = (
    "Claude API",
    "Claude Desktop",
    "claude-haiku",
    "claude-project",
    "CLAUDE_MAP.md",
)

# --- the patterns ----------------------------------------------------------

RE_CLAUDE_MD = re.compile(r"\bCLAUDE\.md\b")
RE_CLAUDE_DIR = re.compile(r"(?:~/|\$HOME/|/home/[\w.-]+/)?\.claude(?:/|\b)")
RE_CLAUDE_CLI = re.compile(
    r"(?<![\w./-])(?:npx\s+)?claude(?:\s+code)?\s+(?:--?[\w-]|\$|/)")

# Claude tool names as bare words.
CLAUDE_TOOL_WORDS = (
    "AskUserQuestion", "TodoWrite", "MultiEdit", "WebFetch", "WebSearch",
    "NotebookEdit", "SlashCommand", "ExitPlanMode",
)
RE_CLAUDE_TOOL_WORD = re.compile(r"\b(?:%s)\b" % "|".join(CLAUDE_TOOL_WORDS))

# Claude tool names in backticks. The backtick has to sit on both sides, so
# `Task<T>` (a C# type) is not a tool name.
#
# The bare backticked `Task` is deliberately NOT in this list: upstream writes
# it for the C# type (pool/skills/dotnet-patterns/SKILL.md:315 "Return `Task`",
# pool/agents/csharp-reviewer.md:43 "return `Task`"), and tools/apply_selection.py
# does not rewrite it either -- renaming it would corrupt real C# code. Claude's
# Task tool is spelled "Task tool" or "Task(subagent_type=...)" upstream.
CLAUDE_TOOL_BACKTICKED = (
    "Read", "Edit", "Write", "Grep", "Glob", "Bash", "MultiEdit",
)
RE_CLAUDE_TOOL_BACKTICK = re.compile(
    r"`(?P<name>%s)`" % "|".join(CLAUDE_TOOL_BACKTICKED))

RE_CLAUDE_CODE = re.compile(r"\bClaude Code\b")

# A slash command in a field that is shown to the user. The trailing guard
# lets a sentence end right behind the token ("use /plan-canvas.") but
# rejects a path ("openspec/specs/...").
RE_SLASH_LOOSE = re.compile(
    r"(?<![\w`/.:\\-])(/[a-z][a-z0-9]*(?:-[a-z0-9]+)*)(?![\w/-])")

# A markdown link: the target is a path, not a command.
RE_MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")

RE_MODEL_KEY = re.compile(r"^\s*model\s*:")

# The Claude tool names an agent may not ask for. `Task` is listed here
# because an agent frontmatter that still asks for `Task` was not renamed to
# omp's `task`; the backticked body form stays excluded (C# type).
CLAUDE_TOOL_NAMES = (
    frozenset(CLAUDE_TOOL_WORDS)
    | frozenset(CLAUDE_TOOL_BACKTICKED)
    | frozenset({"Task"})
)

RESERVED_AGENT_NAMES = frozenset({"main", "sub"})


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def as_text(value):
    """Frontmatter values are strings or lists of strings."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value).strip()
    return str(value).strip()


def whitelist_spans(line):
    """Spans of the Anthropic product tokens inside one line."""
    spans = []
    for token in WHITELIST_TOKENS:
        start = line.find(token)
        while start != -1:
            spans.append((start, start + len(token)))
            start = line.find(token, start + 1)
    return spans


def overlaps(span, spans):
    start, end = span
    for other_start, other_end in spans:
        if start < other_end and other_start < end:
            return True
    return False


def read_text(path):
    """Read a file as UTF-8 text; return None when it is not text."""
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def tree_path(tree, rel):
    """The path of a tree-relative file."""
    return os.path.join(tree, rel.replace("/", os.sep))


def collect_files(tree):
    """Every file under the scanned directories, relative to the tree."""
    out = []
    for scanned in SCAN_DIRS:
        base = os.path.join(tree, scanned)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, tree).replace(os.sep, "/")
                out.append(rel)
    return out


def skill_directories(tree):
    """The direct subdirectories of `skills/` -- one per skill."""
    base = os.path.join(tree, "skills")
    if not os.path.isdir(base):
        return []
    return sorted(name for name in os.listdir(base)
                  if os.path.isdir(os.path.join(base, name))
                  and name not in SKIP_DIRS)


def command_names(tree):
    """The command names this tree ships (`commands/<name>.md`)."""
    base = os.path.join(tree, "commands")
    if not os.path.isdir(base):
        return set()
    return {name[:-3] for name in os.listdir(base)
            if name.endswith(".md") and os.path.isfile(os.path.join(base, name))}


def cropped_command_names(tree):
    """Command names the fork knows but this tree does not ship.

    A narrow profile crops commands. The fork's own catalog files (the
    router skill, the workflow rule) name the commands of every profile, so
    a reference to a cropped command is expected there and is not a break.
    """
    base = os.path.join(REPO_ROOT, "pool", "commands")
    known = set()
    if os.path.isdir(base):
        known = {refscan.runtime_name(name[:-3]) for name in os.listdir(base)
                 if name.endswith(".md")
                 and os.path.isfile(os.path.join(base, name))}
    return known - command_names(tree)


def flat_files(tree, kind):
    """The markdown files directly under `kind/`."""
    base = os.path.join(tree, kind)
    if not os.path.isdir(base):
        return []
    return sorted(name for name in os.listdir(base)
                  if name.endswith(".md")
                  and os.path.isfile(os.path.join(base, name)))


def is_file_name(text, end):
    """True when the token at `end` is followed by a file extension."""
    tail = text[end:]
    return bool(re.match(r"\.\w", tail))


def description_field(block):
    """`(lineno, text, chunks)` of the `description:` field of a block.

    A block scalar keeps its text on the indented lines below the key, so
    those lines belong to the field as well. `chunks` holds the
    `(lineno, text)` of every part, so a token in the folded text can be
    reported on the line it was written on.
    """
    for pos, (lineno, line) in enumerate(block):
        match = mdmeta.RE_KEY.match(line)
        if not match or match.group("key") != "description":
            continue
        parts = [(lineno, match.group("rest"))]
        for nxt_lineno, nxt in block[pos + 1:]:
            if not nxt[:1].isspace():
                break
            parts.append((nxt_lineno, nxt))
        chunks = []
        for part_lineno, part in parts:
            stripped = part.strip()
            if stripped:
                chunks.append((part_lineno, stripped))
        text = " ".join(chunk for _, chunk in chunks)
        return lineno, text, chunks
    return None, "", []


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------

def check_text_rules(rel, text, commands, frontmatter=(), cropped=frozenset(),
                      fork_owned=frozenset()):
    """INV-02, INV-03, INV-04, INV-05, INV-14, INV-15 for one file.

    `frontmatter` holds the line numbers of the first frontmatter block. The
    INV-14 body scan skips them: a `/name` in the frontmatter is the
    `description:` field's business (`check_description_commands`), and the
    two rules must not report the same token twice.
    """
    findings = []
    frontmatter = set(frontmatter)
    lines = text.split("\n")
    fenced = refscan.fenced_lines(lines)
    exempt = rel in EXEMPT_FILES

    for idx, raw in enumerate(lines):
        lineno = idx + 1
        spans = whitelist_spans(raw)

        for match in RE_CLAUDE_MD.finditer(raw):
            if overlaps(match.span(), spans):
                continue
            findings.append({
                "invariant": "INV-02", "file": rel, "line": lineno,
                "token": match.group(0),
                "message": "`CLAUDE.md` is a Claude-harness project file; "
                           "the fork must not point at it",
            })

        for match in RE_CLAUDE_DIR.finditer(raw):
            if overlaps(match.span(), spans):
                continue
            findings.append({
                "invariant": "INV-03", "file": rel, "line": lineno,
                "token": match.group(0),
                "message": "`.claude/` is the Claude-harness configuration "
                           "directory; the fork must not point at it",
            })

        for match in RE_CLAUDE_CLI.finditer(raw):
            if overlaps(match.span(), spans):
                continue
            findings.append({
                "invariant": "INV-04", "file": rel, "line": lineno,
                "token": match.group(0).strip(),
                "message": "invokes the `claude` CLI; the fork runs in omp",
            })

        if not exempt:
            for match in RE_CLAUDE_TOOL_WORD.finditer(raw):
                if overlaps(match.span(), spans):
                    continue
                findings.append({
                    "invariant": "INV-05", "file": rel, "line": lineno,
                    "token": match.group(0),
                    "message": "`%s` is a Claude tool name; omp uses its own "
                               "tool names" % match.group(0),
                })
            for match in RE_CLAUDE_TOOL_BACKTICK.finditer(raw):
                if overlaps(match.span(), spans):
                    continue
                findings.append({
                    "invariant": "INV-05", "file": rel, "line": lineno,
                    "token": match.group(0),
                    "message": "`%s` is a Claude tool name; omp uses its own "
                               "tool names" % match.group("name"),
                })
            for match in RE_CLAUDE_CODE.finditer(raw):
                if overlaps(match.span(), spans):
                    continue
                findings.append({
                    "invariant": "INV-15", "file": rel, "line": lineno,
                    "token": match.group(0),
                    "message": "names the Claude Code harness; the fork "
                               "runs in omp",
                })

        if lineno not in frontmatter:
            findings.extend(check_command_refs(rel, raw, lineno, commands,
                                               idx in fenced, cropped,
                                               fork_owned))

    return findings


def check_command_refs(rel, raw, lineno, commands, in_fence, cropped=frozenset(),
                        fork_owned=frozenset()):
    """INV-14 for one line: is every `/name` a shipped command?"""
    if in_fence:
        # A fenced code block shows literal text, not a pointer.
        return []

    findings = []
    link_spans = [match.span() for match in RE_MD_LINK.finditer(raw)]
    seen = set()

    def report(name, token):
        if name in seen:
            return
        seen.add(name)
        if name in refscan.PATH_NOISE:
            return
        if name in commands:
            return
        if name in cropped and rel in fork_owned:
            # the fork's own catalog names the commands of every profile
            return
        findings.append({
            "invariant": "INV-14", "file": rel, "line": lineno,
            "token": token,
            "message": "`/%s` is not a command this tree ships" % name,
        })

    for match in refscan.RE_CMD_BACK.finditer(raw):
        if overlaps(match.span(), link_spans):
            continue
        report(match.group(1)[1:], match.group(0))

    if refscan.CMD_CUE.search(raw):
        for match in refscan.RE_CMD_INLINE.finditer(raw):
            if overlaps(match.span(), link_spans):
                continue
            report(match.group(1)[1:], match.group(0))

    return findings


def check_description_commands(rel, block, commands, cropped=frozenset(),
                               fork_owned=frozenset()):
    """INV-14 for the `description:` field of a frontmatter block.

    A description is the text omp shows the user; a `/name` in it is a
    command to type, not a path. The field is checked without the cue and
    backtick rules of the body, because upstream hides the pointer to a
    sibling command exactly there.
    """
    findings = []
    lineno, text, chunks = description_field(block)
    if not text:
        return findings
    # Map every offset of the folded text back to the line it came from.
    spans = []
    offset = 0
    for part_lineno, chunk in chunks:
        spans.append((offset, offset + len(chunk), part_lineno))
        offset += len(chunk) + 1  # the joining space

    def line_of(pos):
        for start, end, part_lineno in spans:
            if start <= pos < end:
                return part_lineno
        return lineno

    for match in RE_SLASH_LOOSE.finditer(text):
        name = match.group(1)[1:]
        if is_file_name(text, match.end()):
            continue  # `/spec.md` is a file, not a command
        if name in refscan.PATH_NOISE or name in commands:
            continue
        if name in cropped and rel in fork_owned:
            # the fork's own catalog names the commands of every profile
            continue
        findings.append({
            "invariant": "INV-14", "file": rel, "line": line_of(match.start()),
            "token": match.group(1),
            "message": "`/%s` is not a command this tree ships" % name,
        })
    return findings


def check_frontmatter_model(rel, block):
    """INV-01: a `model:` key in the frontmatter block."""
    findings = []
    for lineno, line in block:
        if RE_MODEL_KEY.match(line):
            findings.append({
                "invariant": "INV-01", "file": rel, "line": lineno,
                "token": line.strip(),
                "message": "`model:` selects the Claude model; omp picks the "
                           "model itself",
            })
    return findings


def check_skills(tree, files, findings):
    """INV-06, INV-07, INV-08."""
    known = set(files)
    for skill in skill_directories(tree):
        rel = "skills/%s/SKILL.md" % skill
        if rel not in known:
            findings.append({
                "invariant": "INV-08", "file": "skills/%s" % skill,
                "line": 1, "token": "SKILL.md",
                "message": "skill directory holds no `SKILL.md`",
            })
            continue
        meta, _ = mdmeta.read_meta_file(tree_path(tree, rel))
        name = as_text(meta.get("name"))
        description = as_text(meta.get("description"))
        if not name:
            findings.append({
                "invariant": "INV-06", "file": rel, "line": 1,
                "token": "name",
                "message": "skill frontmatter has no `name`",
            })
        if not description:
            findings.append({
                "invariant": "INV-06", "file": rel, "line": 1,
                "token": "description",
                "message": "skill frontmatter has no `description`",
            })
        if name and name != skill:
            findings.append({
                "invariant": "INV-07", "file": rel, "line": 1,
                "token": name,
                "message": "skill `name` does not match its directory `%s`"
                           % skill,
            })

    for rel in files:
        base = os.path.basename(rel)
        if base.lower() != "skill.md":
            continue
        parts = rel.split("/")
        if len(parts) != 3:
            findings.append({
                "invariant": "INV-08", "file": rel, "line": 1,
                "token": base,
                "message": "`SKILL.md` must sit directly in "
                           "`skills/<skill>/`",
            })


def check_agents(tree, files, findings):
    """INV-09, INV-10, INV-11."""
    for name in files:
        rel = "agents/%s" % name
        text = read_text(tree_path(tree, rel))
        if text is None:
            continue
        meta, body = mdmeta.parse_frontmatter(text)
        agent_name = as_text(meta.get("name"))
        description = as_text(meta.get("description"))
        stem = name[:-3]
        if not agent_name:
            findings.append({
                "invariant": "INV-09", "file": rel, "line": 1,
                "token": "name",
                "message": "agent frontmatter has no `name`",
            })
        if not description:
            findings.append({
                "invariant": "INV-09", "file": rel, "line": 1,
                "token": "description",
                "message": "agent frontmatter has no `description`",
            })
        if not body.strip():
            findings.append({
                "invariant": "INV-09", "file": rel, "line": 1,
                "token": "body",
                "message": "agent has no body; the body is the system prompt",
            })
        if agent_name and agent_name != stem:
            findings.append({
                "invariant": "INV-10", "file": rel, "line": 1,
                "token": agent_name,
                "message": "agent `name` does not match its file name `%s`"
                           % stem,
            })
        if agent_name in RESERVED_AGENT_NAMES:
            findings.append({
                "invariant": "INV-10", "file": rel, "line": 1,
                "token": agent_name,
                "message": "`%s` is a reserved agent name" % agent_name,
            })
        tools = meta.get("tools")
        for tool in tool_names(tools):
            if tool in CLAUDE_TOOL_NAMES:
                findings.append({
                    "invariant": "INV-11", "file": rel, "line": 1,
                    "token": tool,
                    "message": "`tools:` asks for the Claude tool `%s`; omp "
                               "uses its own tool names" % tool,
                })


def tool_names(value):
    """The tool names of an agent `tools:` value."""
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value]
    else:
        items = [part.strip() for part in re.split(r"[,\s]+", str(value))]
    return [item for item in items if item]


def check_rules(tree, files, findings):
    """INV-12."""
    for name in files:
        rel = "rules/%s" % name
        meta, _ = mdmeta.read_meta_file(tree_path(tree, rel))
        description = as_text(meta.get("description"))
        always_apply = as_text(meta.get("alwaysApply")).lower()
        if not description and always_apply != "true":
            findings.append({
                "invariant": "INV-12", "file": rel, "line": 1,
                "token": "description",
                "message": "rule has neither a `description` nor "
                           "`alwaysApply: true`",
            })


def check_commands(tree, files, findings):
    """INV-13."""
    for name in files:
        rel = "commands/%s" % name
        meta, _ = mdmeta.read_meta_file(tree_path(tree, rel))
        if not as_text(meta.get("description")):
            findings.append({
                "invariant": "INV-13", "file": rel, "line": 1,
                "token": "description",
                "message": "command has no `description`",
            })


def collect(tree):
    """Run every invariant over `tree`; returns the findings."""
    findings = []
    files = collect_files(tree)
    commands = command_names(tree)
    cropped = cropped_command_names(tree)
    fork_owned = refscan.fork_owned_paths()

    for rel in files:
        text = read_text(tree_path(tree, rel))
        if text is None:
            continue  # not a text file
        block = mdmeta.frontmatter_lines(text) if rel.endswith(".md") else []
        findings.extend(check_text_rules(rel, text, commands,
                                         (lineno for lineno, _ in block),
                                         cropped, fork_owned))
        if rel.endswith(".md"):
            findings.extend(check_frontmatter_model(rel, block))
            findings.extend(check_description_commands(rel, block, commands,
                                                       cropped, fork_owned))

    check_skills(tree, files, findings)
    check_agents(tree, flat_files(tree, "agents"), findings)
    check_rules(tree, flat_files(tree, "rules"), findings)
    check_commands(tree, flat_files(tree, "commands"), findings)

    findings.sort(key=lambda f: (f["file"], f["line"], f["invariant"],
                                 f["token"]))
    return files, findings


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------

def report(tree, files, findings, as_json):
    counts = {inv: 0 for inv, _ in INVARIANTS}
    for finding in findings:
        counts[finding["invariant"]] = counts.get(finding["invariant"], 0) + 1

    if as_json:
        payload = {
            "tree": os.path.abspath(tree).replace(os.sep, "/"),
            "scanned_files": len(files),
            "invariants": [
                {
                    "id": inv,
                    "title": title,
                    "ok": counts.get(inv, 0) == 0,
                    "violations": counts.get(inv, 0),
                }
                for inv, title in INVARIANTS
            ],
            "violations": findings,
            "summary": {
                "total": len(INVARIANTS),
                "passed": sum(1 for inv, _ in INVARIANTS
                              if counts.get(inv, 0) == 0),
                "failed": sum(1 for inv, _ in INVARIANTS
                              if counts.get(inv, 0) != 0),
                "violation_count": len(findings),
            },
            "exit_code": 1 if findings else 0,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("tree: %s" % os.path.abspath(tree).replace(os.sep, "/"))
    print("files scanned: %d" % len(files))
    print("")
    for inv, title in INVARIANTS:
        count = counts.get(inv, 0)
        if count:
            print("[FAIL] %s  %s  (%d)" % (inv, title, count))
        else:
            print("[PASS] %s  %s" % (inv, title))
    print("")
    if findings:
        print("violations: %d" % len(findings))
        for finding in findings:
            print("%s:%d: [%s] %s -- %s" % (
                finding["file"], finding["line"], finding["invariant"],
                finding["token"], finding["message"]))
    else:
        print("violations: 0")


def main(argv):
    parser = argparse.ArgumentParser(
        description="Report Claude-harness references left in a materialized "
                    "tree. The tree is never modified.")
    parser.add_argument("--tree", default=REPO_ROOT,
                        help="the tree to scan (default: this repository)")
    parser.add_argument("--json", action="store_true",
                        help="print the report as JSON")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0

    tree = os.path.abspath(args.tree)
    if not os.path.isdir(tree):
        print("error: %s is not a directory" % tree, file=sys.stderr)
        return 2
    if not any(os.path.isdir(os.path.join(tree, d)) for d in SCAN_DIRS):
        print("error: %s holds none of %s" % (tree, ", ".join(SCAN_DIRS)),
              file=sys.stderr)
        return 2

    try:
        files, findings = collect(tree)
    except OSError as exc:
        print("error: cannot inspect %s: %s" % (tree, exc), file=sys.stderr)
        return 2
    except Exception as exc:  # an internal error is not a violation
        print("error: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2

    report(tree, files, findings, args.json)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
