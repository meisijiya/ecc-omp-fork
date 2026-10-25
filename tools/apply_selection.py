#!/usr/bin/env python
"""Materialize the active profile into the plugin's runtime layout.

Inputs
  manifest/groups.json          group -> member classification (all three kinds)
  manifest/selection.json       active profile pointer + extra items
  manifest/profiles/<p>.json    the profile's group/exclude/include choices
  pool/                         upstream snapshot: skills/ commands/ agents/
  own/skills/                   fork-authored skills (always included)
  own/rules/                    fork-authored rules (always included)
  own/patches/<kind>/<name>.md  fork-authored full replacements for upstream assets

Outputs (all at repo root; this IS the omp plugin layout)
  skills/     commands/     agents/     rules/
  manifest/applied.json      what was actually applied (deploy checks this)

Upstream content is not copied byte-for-byte: it carries Claude Code
assumptions that omp cannot honor. Four deterministic transforms run over it:

  1. agents lose the Claude-only `model: sonnet|opus|haiku` frontmatter line
     (omp has no such model aliases; an unresolvable model makes the agent
     unusable).
  2. skills/commands/agents get their Claude tool names rewritten to omp's
     names, and references to Claude-only mechanisms (PreToolUse/PostToolUse
     hooks, settings.json, .claude/** artifact directories,
     AskUserQuestion) are dropped or replaced. Agents keep their frontmatter
     declarations, skip the line drops and use a narrower tool-name set than
     skills and commands. This has to live here rather than as hand edits,
     because every upstream sync re-materializes these files and would
     otherwise overwrite the patches.
  3. references to assets that the *active profile* does not ship are removed
     (tools/refscan.py). Upstream content points at skills and commands that
     exist only in the full upstream install; in this fork they are dead
     pointers the model would chase. The repair runs against the resolved
     profile, so a pointer that another profile does ship survives there.
  4. targeted fix-ups rewrite residual upstream wording in single files
     (FIXUPS). They run after the rewrites and before the reference repair,
     so their `old` text is the text the rewrite channel produced.

Fork-authored content (own/skills, own/rules, own/patches) is copied
verbatim and must itself be free of dangling references -- that is what
tools/check_refs.py gates.
"""

import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refscan  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "pool")
OWN = os.path.join(ROOT, "own")
KINDS = ("skills", "commands", "agents")
RUNTIME = ("skills", "commands", "agents", "rules")

# ---------------------------------------------------------------------------
# Claude Code -> omp rewrites applied to materialized skill/command/agent text.
# Ordered: earlier rules win, so put the most specific patterns first.
# ---------------------------------------------------------------------------
TOOL_RENAMES = [
    (r"\bAskUserQuestion\b", "ask"),
    (r"\bTodoWrite\b", "todo"),
    (r"\bRead tool\b", "read tool"),
    (r"\bEdit tool\b", "edit tool"),
    (r"\bWrite tool\b", "write tool"),
    (r"\bGrep tool\b", "grep tool"),
    (r"\bGlob tool\b", "glob tool"),
    (r"\bBash tool\b", "bash tool"),
    # Claude's Task tool is spelled "Task tool" or "Task(subagent_type=...)"
    # upstream; the bare backticked `Task` is the C# type (pool/skills/
    # dotnet-patterns/SKILL.md:315, pool/agents/csharp-reviewer.md:43), so
    # rewriting it would corrupt real code.
    (r"\bTask tool\b", "task tool"),
    (r"\bthe Read\b", "the read"),
    (r"\bthe Edit\b", "the edit"),
    (r"\bthe Write\b", "the write"),
    (r"\bthe Grep\b", "the grep"),
    (r"\bthe Glob\b", "the glob"),
    (r"\bthe Bash\b", "the bash"),
    # "the Task" is Claude's tool in skills and commands, but upstream agent
    # prose uses it for the assignment (pool/agents/agent-evaluator.md:38
    # "Understand the Task"), so AGENT_TOOL_RENAMES drops this rule. In the
    # materialized skills and commands it never fires: pool/commands/plan.md
    # "the Task tool" already became "the task tool" above.
    (r"\bthe Task\b", "the task"),
    (r"`Read`", "`read`"),
    (r"`Edit`", "`edit`"),
    (r"`Write`", "`write`"),
    (r"`Grep`", "`grep`"),
    (r"`Glob`", "`glob`"),
    (r"`Bash`", "`bash`"),
    (r"\bMultiEdit\b", "edit"),
]

# Lines that instruct the model to use a mechanism omp does not have.
# Kept narrow: each pattern must be anchored to the Claude-specific context
# (a Claude slash command, a Claude hook name, a Claude config path) so that
# ordinary prose mentioning e.g. "npm init" survives.
LINE_DROP_PATTERNS = [
    r"^\s*allowed-tools:",
    r"PreToolUse\[",
    r"^\s*PostToolUse\b",
    r"^\s*UserPromptSubmit\b",
    r"^\s*SessionStart\b",
    # The path rename runs before the line drop, so the detector path is
    # already spelled `.omp/package-manager.json` when the drop is checked.
    r"\.claude/package-manager\.json",
    r"\.omp/package-manager\.json",
    r"\bCLAUDE_PACKAGE_MANAGER\b",
    r"`/plan-canvas`",
    r"`/review-pr`",
    r"`/orch-review`",
    r"`/multi-plan`",
    r"`/multi-execute`",
    r"`/multi-frontend`",
    r"`/multi-workflow`",
    r"`/loop-start`",
    r"`/loop-status`",
    r"`/santa-loop`",
    r"`/init`",
    r"`/simplify`",
    r"`/security-scan`",
]

# Path rewrites. The fork is omp-native: Claude's context file becomes
# AGENTS.md, and Claude's artifact directories become a plain docs/ tree.
# The rewrites are applied consistently across every command and skill, so
# the commands still refer to each other's outputs.
PATH_RENAMES = [
    (r"\bCLAUDE\.md\b", "AGENTS.md"),
    # the rename above turns "a CLAUDE.md" into "a AGENTS.md"; restore the
    # article. The leading \b keeps "via AGENTS.md" (upstream
    # pool/skills/inherit-legacy-style/SKILL.md) from becoming "vi an ...".
    (r"\ba AGENTS\.md\b", "an AGENTS.md"),
    (r"\ba `AGENTS\.md`", "an `AGENTS.md`"),
    (r"\.claude/PRPs/prds", "docs/prp/prds"),
    (r"\.claude/PRPs/plans", "docs/prp/plans"),
    (r"\.claude/PRPs/reports", "docs/prp/reports"),
    (r"\.claude/PRPs/reviews", "docs/prp/reviews"),
    (r"\.claude/prds", "docs/prds"),
    (r"\.claude/plans", "docs/plans"),
    (r"\.claude/reviews", "docs/reviews"),
    (r"\.claude/tdd", "docs/tdd"),
    (r"\.claude/docs/", "docs/"),
    (r"\.claude/PRPs/", "docs/prp/"),
    # The remaining `.claude` paths are the harness directories themselves.
    # omp keeps its user-level state in `~/.omp/agent/` (user skills live in
    # `~/.omp/agent/skills/`) and its project-level state in `.omp/`, so the
    # directories move rather than disappear. The settings file has no
    # same-named counterpart: the omp config is `config.yml`, at
    # `~/.omp/agent/config.yml` for the user level and `.omp/config.yml` for
    # the project level. These come last so the more specific
    # `.claude/docs/` and `.claude/PRPs/` rules above keep winning, and the
    # user-level rules come before the generic directory rule so they are
    # not rewritten to `~/.omp/skills/` or `.omp/settings.json`.
    (r"~/\.claude/settings\.json", "~/.omp/agent/config.yml"),
    (r"~/\.claude\b", "~/.omp/agent"),
    (r"\.claude/settings\.json", ".omp/config.yml"),
    (r"\.claude\b", ".omp"),
]

# Claude Code tool names -> omp tool names, for the `tools:` frontmatter of
# agents. omp's own tool names are the snake_case ones (read, edit, write,
# bash, grep, glob, task, todo, ask, web_search). A Claude name that has no
# omp counterpart is dropped: omp selects "no built-ins" for a declaration
# whose names all resolve to nothing, which would leave the agent unable to
# do anything at all.
AGENT_TOOL_MAP = {
    "read": "read",
    "write": "write",
    "edit": "edit",
    "multiedit": "edit",
    "bash": "bash",
    "grep": "grep",
    "glob": "glob",
    "task": "task",
    "todowrite": "todo",
    "askuserquestion": "ask",
    "websearch": "web_search",
}
# Claude tools with no omp counterpart.
AGENT_TOOL_DROP = {"webfetch", "notebookedit", "slashcommand", "exitplanmode"}

# Agent prose takes the same tool-name rewrites as skills and commands, minus
# the rules that collide with ordinary English. "the Task" is the one to
# drop: upstream agents mean the assignment by it (pool/agents/
# agent-evaluator.md:38 "Understand the Task"), not Claude's Task tool.
AGENT_TOOL_RULE_EXCLUSIONS = {r"\bthe Task\b"}
AGENT_TOOL_RENAMES = [
    rule for rule in TOOL_RENAMES if rule[0] not in AGENT_TOOL_RULE_EXCLUSIONS
]


def load_json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def active_selection():
    """Merge the active profile with the extra items recorded in selection.json."""
    selection_path = os.path.join(ROOT, "manifest", "selection.json")
    if not os.path.isfile(selection_path):
        raise SystemExit("manifest/selection.json is missing")
    selection = load_json("manifest", "selection.json")
    if "active_profile" not in selection:
        raise SystemExit("manifest/selection.json has no 'active_profile' field")
    profile_name = selection["active_profile"]
    profile_path = os.path.join(ROOT, "manifest", "profiles", profile_name + ".json")
    if not os.path.isfile(profile_path):
        raise SystemExit(f"unknown profile {profile_name!r}: {profile_path} not found")
    profile = load_json("manifest", "profiles", profile_name + ".json")
    if profile.get("profile") != profile_name:
        raise SystemExit(
            f"profile identity mismatch: file {profile_name}.json declares "
            f"{profile.get('profile')!r}"
        )
    extra = selection.get("extra", {})
    unknown_keys = set(extra) - set(KINDS)
    if unknown_keys:
        raise SystemExit(
            f"manifest/selection.json extra has unknown keys {sorted(unknown_keys)};"
            f" allowed: {sorted(KINDS)}"
        )
    merged = {}
    for kind in KINDS:
        base = profile.get(kind, {})
        merged[kind] = {
            "groups": list(base.get("groups", [])),
            "exclude": list(base.get("exclude", [])),
            "include": list(base.get("include", [])) + list(extra.get(kind, [])),
        }
    return profile_name, merged


def pool_members(kind):
    d = os.path.join(POOL, kind)
    if not os.path.isdir(d):
        return set()
    if kind == "skills":
        out = set()
        for n in os.listdir(d):
            if os.path.isdir(os.path.join(d, n)) and os.path.isfile(os.path.join(d, n, "SKILL.md")):
                out.add(n)
        return out
    return {os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".md")}


def resolve(group_map, sel, kind, known):
    """Resolve one asset kind to a concrete, validated member list."""
    picked = []
    seen = set()
    for code in sel["groups"]:
        if code not in group_map:
            raise SystemExit(f"unknown group {code!r} for {kind}")
        for name in group_map[code]["members"]:
            if name in seen:
                raise SystemExit(f"{kind}: {name!r} appears in more than one group")
            seen.add(name)
            picked.append(name)

    exclude = set(sel["exclude"])
    unknown_exclude = exclude - seen
    if unknown_exclude:
        raise SystemExit(
            f"{kind}: exclude lists names that are not in the selected groups: "
            f"{sorted(unknown_exclude)}"
        )

    result = [n for n in picked if n not in exclude]
    for n in sel["include"]:
        if n not in result:
            result.append(n)
    missing = [n for n in result if n not in known]
    if missing:
        raise SystemExit(f"{kind}: selected but not present in pool: {missing}")
    return result


def strip_frontmatter_key(text, key):
    """Remove a top-level frontmatter key without touching the body.

    The key may be the last line of the frontmatter, in which case it has no
    trailing newline -- matching on `key:.*\\n` alone would silently keep it.
    """
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm = text[3:end]
    rest = text[end:]
    fm = re.sub(r"^%s:[^\n]*\n?" % re.escape(key), "", fm, flags=re.M)
    return "---" + fm + rest


def set_frontmatter_name(text, name):
    """Set the `name:` field of the frontmatter of `text`.

    The runtime tree renames every asset of the upstream pool, so the name
    an asset declares has to be the name it is shipped under. Only the
    first `name:` line inside the frontmatter is touched; a file without
    frontmatter is returned unchanged.
    """
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm = text[3:end]
    rest = text[end:]
    fm, hits = re.subn(r"^name:[^\n]*$", "name: " + name, fm, count=1,
                       flags=re.M)
    if not hits:
        return text
    return "---" + fm + rest


def rewrite_agent_tools(text):
    """Rewrite the `tools:` frontmatter entry to omp tool names.

    Upstream agents declare Claude Code tool names (`Read, Grep, Glob, Bash`).
    omp's tool names are snake_case (`read`, `grep`, `glob`, `bash`), and a
    declaration whose names all fail to resolve selects no built-ins at all,
    which would leave the agent unable to act. Claude-only tools are dropped;
    MCP tool names (`mcp__server__tool`) are left untouched because omp
    namespaces MCP tools the same way.
    """
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm = text[3:end]
    rest = text[end:]

    def repl(m):
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        out = []
        for n in names:
            if n.startswith("mcp__") or n.startswith("xd://"):
                out.append(n)
                continue
            key = n.lower()
            if key in AGENT_TOOL_DROP:
                continue
            mapped = AGENT_TOOL_MAP.get(key)
            if mapped and mapped not in out:
                out.append(mapped)
        if not out:
            # No usable tool left: drop the key so omp falls back to the
            # default built-in toolset instead of an empty one.
            return ""
        return "tools: " + ", ".join(out) + "\n"

    fm = re.sub(r"^tools:[ \t]*(.*)$", repl, fm, count=1, flags=re.M)
    return "---" + fm + rest


def apply_renames(text, tool_renames):
    """Apply the tool-name rewrites, then the path rewrites.

    The path rewrites are ordered among themselves: the CLAUDE.md ->
    AGENTS.md rename has to run before the article fix-up that follows it.
    """
    for pattern, repl in tool_renames:
        text = re.sub(pattern, repl, text)
    for pattern, repl in PATH_RENAMES:
        text = re.sub(pattern, repl, text)
    return text


def adapt_text(text, paths_only=False):
    """Rewrite Claude Code tool names and drop Claude-only mechanisms.

    `paths_only` applies just the path rewrites, which are safe for scripts
    and other non-prose files; the tool-name rewrites are prose-level and
    only make sense in markdown.
    """
    if paths_only:
        return apply_renames(text, ())
    text = apply_renames(text, TOOL_RENAMES)
    kept = []
    for line in text.split("\n"):
        if any(re.search(p, line) for p in LINE_DROP_PATTERNS):
            continue
        kept.append(line)
    return "\n".join(kept)


def adapt_agent_text(text):
    """Rewrite agent prose: tool names and paths, but no line drops.

    The drop patterns are line-anchored, so a hit takes the whole line with
    it, and an agent's frontmatter declarations (`allowed-tools:`) sit on
    their own lines. The patterns match no agent in pool/agents today (the
    Claude hook mentions in chief-of-staff.md and harness-optimizer.md are
    mid-line, and neither agent ships in this profile), so skipping the
    drops costs nothing while keeping agent frontmatter intact.
    """
    return apply_renames(text, AGENT_TOOL_RENAMES)


# Targeted rewrites for single materialized files, keyed by the
# repo-relative path the file has in the runtime tree ("skills/<name>/SKILL.md",
# "commands/<name>.md", "agents/<name>.md"). Kept as data rather than as
# hand-edited files so that an upstream sync cannot silently undo them.
#
# Each entry lists literal (old, new) pairs, applied in order after the
# rewrite channel and before the reference repair, so `old` is the text the
# rewrite channel produced. A pair whose `old` is not in the file is skipped:
# upstream text drifts, and a stale fix-up must not break materialization.
FIXUPS = {
    "skills/verification-loop/SKILL.md": [
        (
            "Run: /verify",
            "Run the six-phase verification loop described above "
            "(build / type check / lint / tests / secret scan / diff review).",
        ),
        (
            "## Integration with Hooks\n\n"
            "This skill complements PostToolUse hooks but provides deeper verification.\n"
            "Hooks catch issues immediately; this skill provides comprehensive review.",
            "## Relationship to other verification assets\n\n"
            "This skill is the general six-phase loop. Language- and framework-specific\n"
            "gates live in their own skills (`springboot-verification`,\n"
            "`django-verification`, `python-testing`, `kotlin-testing`, ...); read\n"
            "those instead when the project already defines them.",
        ),
        # The skill is tool-agnostic, so its description must not name the
        # product it was written for.
        (
            "a Claude Code session's work",
            "the current session's work",
        ),
        (
            "A comprehensive verification system for Claude Code sessions.",
            "A comprehensive verification system for coding sessions.",
        ),
    ],
    "skills/codebase-onboarding/SKILL.md": [
        (
            "setting up Claude Code for the first time in a repo.",
            "setting up omp for the first time in a repo.",
        ),
        (
            "setting up Claude Code in an existing repo for the first time.",
            "setting up omp in an existing repo for the first time.",
        ),
        (
            "First time opening a project with Claude Code",
            "First time opening a project with omp",
        ),
    ],
    "skills/tdd-workflow/SKILL.md": [
        (
            "If the repository already uses Claude-specific local artifacts, the "
            "`docs/tdd/` location is also acceptable.",
            "If the repository already keeps its TDD evidence in a local "
            "directory, that location is also acceptable.",
        ),
        # Upstream points at a detector script that ships with the ECC
        # repository. This fork does not carry it, so the step is replaced
        # by the same detection the sibling commands describe: read the
        # lockfile, then the packageManager field.
        (
            "1. **Run the package-manager detector** (ships with ECC):\n"
            "\n"
            "   ```bash\n"
            "   node scripts/setup-package-manager.js --detect\n"
            "   ```\n"
            "\n"
            "\n",
            "1. **Detect the package manager** from the lockfile or the\n"
            "   `packageManager` field:\n"
            "\n"
            "   | File Exists | Package Manager | Runner |\n"
            "   |---|---|---|\n"
            "   | `bun.lockb` | bun | `bun run` |\n"
            "   | `pnpm-lock.yaml` | pnpm | `pnpm run` |\n"
            "   | `yarn.lock` | yarn | `yarn` |\n"
            "   | `package-lock.json` | npm | `npm run` |\n"
            "\n",
        ),
    ],
    "skills/test-collaboration/SKILL.md": [
        (
            "such as `AGENTS.md`, `AGENTS.md`, and `CLAUDE_MAP.md`.",
            "such as `AGENTS.md` and `CLAUDE_MAP.md`.",
        ),
    ],
    "skills/coding-standards/SKILL.md": [
        # Upstream points at its own nested rules file, which this fork does
        # not carry: the repair pass drops the whole bullet. The fork ships
        # the equivalent as a flat rule, so the bullet is repointed there
        # instead of being lost.
        (
            "- Use `rules/common/coding-style.md` when you need the shortest "
            "reusable rule layer instead of a full skill walkthrough.",
            "- Use `rule://fork-coding-style` when you need the shortest "
            "reusable rule layer instead of a full skill walkthrough.",
        ),
    ],
    "skills/docker-patterns/SKILL.md": [
        # The two environment variables are set by the upstream harness whose
        # compose file the section above no longer carries. Name the knob,
        # not the variable.
        (
            "with `ECC_TMPFS_SIZE`; `ECC_WORKSPACE_SIZE` separately controls "
            "the private\n  workspace mount.",
            "with the tmpfs size option; a separate option controls the "
            "private\n  workspace mount.",
        ),
        # The real-CLI services were defined in the harness section that was
        # dropped, so the surviving sentence has no referent left.
        (
            "- Keep the default real-CLI services on `network_mode: none`.",
            "- Keep the default services on `network_mode: none`.",
        ),
    ],
    "commands/aside.md": [
        ("while Claude is working", "while the assistant is working"),
        ("code Claude is currently editing",
         "code the assistant is currently editing"),
        ("before Claude proceeds", "before the assistant proceeds"),
    ],
    "commands/plan.md": [
        # The upstream description points at two upstream-only commands
        # (`/multi-plan`, `/plan-canvas`). The fork ships neither, and a
        # description that names a command the runtime does not have sends
        # the model after a command that does not exist. The fork's sibling
        # command for the PRD-first flow is `/plan-prd`, and it ships in
        # every profile.
        (
            "Use for a single-model inline or PRD-driven implementation plan; "
            "for a dual-model (Codex/Antigravity) plan use /multi-plan, and "
            "for visual annotate-and-approve review of the resulting plan "
            "use /plan-canvas.",
            "Use for a single-model inline or PRD-driven implementation plan; "
            "for a lean PRD first use /plan-prd.",
        ),
        # The line that mentioned the browser plan canvas was dropped with
        # the rest of the `/plan-canvas` block, which left half a sentence
        # behind ("you can open the / the user annotates the plan in
        # place..."). The confirmation flow is already stated in the
        # sentence above, so the leftover quote goes as a whole.
        (
            "> **Visual review:** instead of asking for a typed confirmation, "
            "you can open the\n> the user annotates the plan in place and "
            "clicks **Approve plan** or **Request\n> changes**, which arrives "
            "as your confirmation signal.\n\n",
            "",
        ),
    ],
    "commands/code-review.md": [
        # Same as `/plan`: the upstream description points at `/review-pr`
        # and `/orch-review`, which the fork does not ship.
        (
            "Use for a step-by-step PRP-style checklist review; for a "
            "multi-agent pass use /review-pr, and for the "
            "adversarially-verified Workflow pass use /orch-review.",
            "Use for a step-by-step PRP-style checklist review; for a "
            "multi-agent pass dispatch the `code-reviewer` agent.",
        ),
    ],
    "skills/dotnet-patterns/SKILL.md": [
        # The gate reads a backticked `Task` as the Claude Code tool name.
        # Here it is the C# type, so it is written out in full: the
        # anti-pattern row keeps pointing at the real return type.
        (
            "| `async void` methods | Return `Task` (except event handlers) |",
            "| `async void` methods | Return `System.Threading.Tasks.Task` "
            "(except event handlers) |",
        ),
    ],
    "agents/csharp-reviewer.md": [
        # Same as the dotnet-patterns row: `Task` is the C# type, and the
        # backticked spelling collides with the Claude Code tool name.
        (
            "- **Fire-and-forget**: `async void` except event handlers — "
            "return `Task`",
            "- **Fire-and-forget**: `async void` except event handlers — "
            "return `System.Threading.Tasks.Task`",
        ),
    ],
    "agents/opensource-packager.md": [
        # This agent writes the packaging for a repository that the user then
        # drives with the fork's harness, so every "Claude Code" mention
        # becomes "omp". The generated context file is `AGENTS.md` after the
        # path rename, and the start command is the fork's own binary.
        (
            "Using with Claude Code",
            "Using with omp",
        ),
        (
            "Using Claude Code? AGENTS.md has all the context.",
            "Using omp? AGENTS.md has all the context.",
        ),
        (
            "immediately usable with Claude Code.",
            "immediately usable with omp.",
        ),
        (
            "especially with Claude Code.",
            "especially with omp.",
        ),
        (
            "gives Claude Code full context",
            "gives omp full context",
        ),
        (
            "claude    # Start Claude Code — reads AGENTS.md automatically",
            "omp    # Start omp — reads AGENTS.md automatically",
        ),
        # The CONTRIBUTING checklist names the README section added above.
        # It quotes the section title without "with", so the shorter form
        # needs its own pair.
        (
            "Using Claude Code",
            "Using with omp",
        ),
    ],
    "skills/agent-eval/SKILL.md": [
        # The skill compares third-party coding agents, so the name stays a
        # product name; the tool identifies it by its agent id, which the
        # same file already uses in the command line and the result table.
        (
            "(Claude Code, Aider, Codex, etc.)",
            "(the claude-code agent, Aider, Codex, etc.)",
        ),
    ],
    "skills/blueprint/SKILL.md": [
        # Here "Claude Code" is the harness itself, so it becomes omp; the
        # skill loader in this fork is omp's native Markdown skill loader.
        (
            "Nothing runs on install or invocation beyond Claude Code's "
            "native Markdown skill loader.",
            "Nothing runs on install or invocation beyond omp's native "
            "Markdown skill loader.",
        ),
        # The requirement names the harness that runs the skill; the fork
        # ships the skill as a file, not as a slash command.
        (
            "- Claude Code (for `/blueprint` slash command)",
            "- omp (for the `blueprint` skill)",
        ),
    ],
    "skills/living-docs-governance/SKILL.md": [
        # Upstream contrasts the harness that is running with the other
        # instruction surfaces. In this fork the running harness is omp, and
        # `AGENTS.md` is its context file, so the bullet names omp instead
        # of the harness the file was written for.
        (
            "- Claude Code projects commonly use `AGENTS.md`.",
            "- This fork's harness (omp) reads `AGENTS.md` (project) and "
            "`~/.omp/agent/AGENTS.md` (user level).",
        ),
        # The path rename turned the upstream list into a duplicated entry.
        (
            "- harness instructions such as `AGENTS.md`, `AGENTS.md`, "
            "`.cursor/rules`, or their equivalent;",
            "- harness instructions such as `AGENTS.md`, `.cursor/rules`, or "
            "their equivalent;",
        ),
    ],
    "skills/product-capability/SKILL.md": [
        # The list names the harnesses a plan can be reused in; the fork's
        # own harness replaces the one the file was written for.
        (
            "- The resulting plan is reusable across Claude Code, Codex, "
            "Cursor, OpenCode, and ECC 2.0 planning surfaces.",
            "- The resulting plan is reusable across omp, Codex, Cursor, "
            "OpenCode, and ECC 2.0 planning surfaces.",
        ),
    ],
}


def apply_fixups(text, rel_path):
    """Apply the path-keyed fix-ups to one materialized file."""
    for old, new in FIXUPS.get(rel_path, ()):
        if old in text:
            text = text.replace(old, new)
    return text


# Upstream sections that document the upstream ECC repository's own
# development harness. Those files do not travel with this fork, so the
# text points at paths that exist nowhere in the runtime tree. Each entry
# names the heading that opens the block and the heading that closes it;
# the closing heading is kept.
DROP_SECTIONS = {
    "skills/docker-patterns/SKILL.md": [
        ("### Exercise the ECC Plugin Setup Harness", "## .dockerignore"),
    ],
}


def drop_sections(text, rel_path):
    """Remove the heading-bounded blocks listed for `rel_path`.

    A block runs from the heading that opens it up to, but not including,
    the heading that closes it. A pair whose headings are not both present
    is left alone: upstream text drifts, and a stale entry must not delete
    the wrong range.
    """
    for opener, closer in DROP_SECTIONS.get(rel_path, ()):
        lines = text.split("\n")
        try:
            first = next(i for i, line in enumerate(lines)
                         if line.strip() == opener)
            last = next(i for i, line in enumerate(lines)
                        if i > first and line.strip() == closer)
        except StopIteration:
            continue
        del lines[first:last]
        text = "\n".join(lines)
    return text


def patch_source(kind, name):
    """Return a fork-authored full replacement for an upstream asset, if any."""
    p = os.path.join(OWN, "patches", kind, name + ".md")
    return p if os.path.isfile(p) else None


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


def rename_patched_skill(directory, runtime):
    """Give a fork replacement the name it is shipped under.

    A patch replaces an upstream asset, so it is copied into the runtime
    directory of that asset; the name it declares has to match the
    directory it lands in.
    """
    p = os.path.join(directory, "SKILL.md")
    if not os.path.isfile(p):
        return
    text = open(p, encoding="utf-8").read()
    write_text(p, set_frontmatter_name(text, runtime))


def materialize_skills(names, report, ctx):
    out = os.path.join(ROOT, "skills")
    tmp = out + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    count = 0
    for n in names:
        rt = refscan.runtime_name(n)
        patch = patch_source("skills", n)
        if patch:
            shutil.copytree(patch, os.path.join(tmp, rt))
            rename_patched_skill(os.path.join(tmp, rt), rt)
            report.append(f"  patched skill (fork replacement): {n}")
        else:
            src = os.path.join(POOL, "skills", n)
            dst = os.path.join(tmp, rt)
            shutil.copytree(src, dst)
            for root, _dirs, files in os.walk(dst):
                for f in files:
                    p = os.path.join(root, f)
                    if f.endswith(".md"):
                        text = open(p, encoding="utf-8").read()
                        text = adapt_text(text)
                        # relative links are resolved against the path the
                        # file will have in the runtime tree, not against the
                        # pool snapshot it was copied from
                        rel = os.path.relpath(p, dst).replace(os.sep, "/")
                        text = drop_sections(text, "skills/%s/%s" % (n, rel))
                        text = apply_fixups(text, "skills/%s/%s" % (n, rel))
                        if rel == "SKILL.md":
                            text = set_frontmatter_name(text, rt)
                        base = refscan.link_context("skills/%s/%s" % (rt, rel))
                        text, notes = refscan.repair_text(
                            text, ctx["mat"], ctx["pool"],
                            owner=rt, external=ctx["external"],
                            link_base=base["base"] if base else None,
                            link_exists=refscan.source_exists)
                        for note in notes:
                            report.append(
                                f"  skills/{rt}/{os.path.relpath(p, dst)}:"
                                f"{note['line']}: {note['action']} "
                                f"`{note['name']}`")
                        write_text(p, text)
                    elif f.endswith((".py", ".sh", ".js", ".mjs", ".ts")):
                        text = open(p, encoding="utf-8", errors="ignore").read()
                        write_text(p, adapt_text(text, paths_only=True))
        count += 1
    own = os.path.join(OWN, "skills")
    own_count = 0
    if os.path.isdir(own):
        for n in sorted(os.listdir(own)):
            src = os.path.join(own, n)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(tmp, n))
                own_count += 1
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.rename(tmp, out)
    return count, own_count


def materialize_commands(names, report, ctx):
    out = os.path.join(ROOT, "commands")
    tmp = out + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    count = 0
    for n in names:
        rt = refscan.runtime_name(n)
        patch = patch_source("commands", n)
        dst = os.path.join(tmp, rt + ".md")
        if patch:
            shutil.copy2(patch, dst)
            report.append(f"  patched command (fork replacement): {n}")
        else:
            src = os.path.join(POOL, "commands", n + ".md")
            text = open(src, encoding="utf-8").read()
            text = adapt_text(text)
            text = apply_fixups(text, "commands/%s.md" % n)
            text, notes = refscan.repair_text(
                text, ctx["mat"], ctx["pool"],
                owner=rt, external=ctx["external"], owner_kind="command",
                link_base="commands", link_exists=refscan.source_exists)
            for note in notes:
                report.append(f"  commands/{rt}.md:{note['line']}: "
                              f"{note['action']} `{note['name']}`")
            write_text(dst, text)
        count += 1
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.rename(tmp, out)
    return count


def materialize_agents(names, report, ctx):
    out = os.path.join(ROOT, "agents")
    tmp = out + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    count = 0
    for n in names:
        rt = refscan.runtime_name(n)
        patch = patch_source("agents", n)
        dst = os.path.join(tmp, rt + ".md")
        if patch:
            shutil.copy2(patch, dst)
            text = open(dst, encoding="utf-8").read()
            write_text(dst, set_frontmatter_name(text, rt))
            report.append(f"  patched agent (fork replacement): {n}")
        else:
            src = os.path.join(POOL, "agents", n + ".md")
            text = open(src, encoding="utf-8").read()
            text = strip_frontmatter_key(text, "model")
            text = rewrite_agent_tools(text)
            text = adapt_agent_text(text)
            text = apply_fixups(text, "agents/%s.md" % n)
            text = set_frontmatter_name(text, rt)
            text, notes = refscan.repair_text(
                text, ctx["mat"], ctx["pool"],
                owner=rt, external=ctx["external"], owner_kind="agent",
                link_base="agents", link_exists=refscan.source_exists)
            for note in notes:
                report.append(f"  agents/{rt}.md:{note['line']}: "
                              f"{note['action']} `{note['name']}`")
            write_text(dst, text)
        count += 1
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.rename(tmp, out)
    return count


def materialize_rules():
    out = os.path.join(ROOT, "rules")
    tmp = out + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    own = os.path.join(OWN, "rules")
    count = 0
    if os.path.isdir(own):
        for f in sorted(os.listdir(own)):
            if f.endswith(".md"):
                shutil.copy2(os.path.join(own, f), os.path.join(tmp, f))
                count += 1
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.rename(tmp, out)
    return count


def main():
    groups = load_json("manifest", "groups.json")
    profile_name, sel = active_selection()
    report = []
    print(f"profile: {profile_name}")

    # Resolve every kind first: the reference repair has to know the *final*
    # asset set, otherwise a skill materialized before the commands would be
    # judged against a half-built tree.
    resolved = {}
    for kind in KINDS:
        known = pool_members(kind)
        declared = set()
        for g in groups[kind].values():
            declared |= set(g["members"])
        if declared != known:
            raise SystemExit(
                f"{kind}: groups declare {len(declared)} members but pool has {len(known)};"
                f" only-in-groups={sorted(declared - known)};"
                f" only-in-pool={sorted(known - declared)}"
            )
        resolved[kind] = resolve(groups[kind], sel[kind], kind, known)

    own_skills = os.path.join(OWN, "skills")
    own_rules = os.path.join(OWN, "rules")
    # the materialized set is spelled the way the runtime tree spells it:
    # every asset of the upstream pool carries the prefix of this fork
    mat = {
        "skills": {refscan.runtime_name(n) for n in resolved["skills"]} | (
            {n for n in os.listdir(own_skills)
             if os.path.isdir(os.path.join(own_skills, n))}
            if os.path.isdir(own_skills) else set()
        ),
        "commands": {refscan.runtime_name(n) for n in resolved["commands"]},
        "agents": {refscan.runtime_name(n) for n in resolved["agents"]},
        "rules": ({os.path.splitext(f)[0] for f in os.listdir(own_rules)
                   if f.endswith(".md")}
                  if os.path.isdir(own_rules) else set()),
    }
    pool = refscan.pool_sets()
    ctx = {
        "mat": mat,
        "pool": pool,
        "external": refscan.external_refs(),
    }

    counts = {}
    for kind in KINDS:
        names = resolved[kind]
        if kind == "skills":
            pool_count, own_count = materialize_skills(names, report, ctx)
            counts["skills"] = pool_count
            counts["skills_own"] = own_count
            print(f"skills: {pool_count} from pool + {own_count} fork-owned")
        elif kind == "commands":
            counts["commands"] = materialize_commands(names, report, ctx)
            print(f"commands: {counts['commands']} materialized")
        else:
            counts["agents"] = materialize_agents(names, report, ctx)
            print(f"agents: {counts['agents']} materialized")

    counts["rules"] = materialize_rules()
    print(f"rules: {counts['rules']} materialized")

    applied = {
        "profile": profile_name,
        "extra": sel,
        "counts": counts,
    }
    write_text(
        os.path.join(ROOT, "manifest", "applied.json"),
        json.dumps(applied, ensure_ascii=False, indent=2) + "\n",
    )

    if report:
        print("\n".join(report))


if __name__ == "__main__":
    main()
