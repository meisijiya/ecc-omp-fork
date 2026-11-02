#!/usr/bin/env python
"""Declarative rewrites that turn an absorbed skill into an omp-safe one.

`tools/sync_absorbed.py` fetches a third-party skill, runs the rules below,
and stores the rewritten copy under `absorbed/<source>/`.  The rules exist
because those skills were written for other harnesses:

  * slash triggers (`Use for /correct.`) name commands this fork never ships
    -- ADR-0008 keeps commands out of the runtime tree, so INV-14 would
    report every one of them.
  * `.claude/`, `CLAUDE.md`, `.codex/` and `Claude` wording is what INV-02,
    INV-03 and INV-15 forbid.
  * `disable-model-invocation:` and `paths:` are host-specific frontmatter
    keys; omp ignores them and they only add noise.
  * sibling-skill links (`../principle-foo/SKILL.md`, "skills in this pack")
    point at files this fork does not ship.

A rule is `(find, replace, note)` where `find` is a regular expression that
MUST match exactly once.  A miss is drift: upstream reworded the sentence,
the rewrite no longer applies, and `sync_absorbed.py` fails instead of
shipping a half-adapted skill.  Order matters: later rules see the output of
earlier ones.

`SOURCE_RULES` holds rules that apply to every markdown file of a source and
may match many times (`(find, replace, note, expected)`).  They exist for
whole-tree conventions -- a shared knowledge base referenced from a dozen
skills, a marketplace-only frontmatter key -- where one rule per occurrence
would be noise.  The expected total is what `{prefix}`-rewritten source trees
must reproduce: a different count means upstream reworded the text and the
rule has to be revisited, exactly like the exactly-once rules above.
"""

import re

import refscan

# Keys are "<source>/<path inside the source repo>".
RULES = {
    "pstack/skills/correct/SKILL.md": [
        (r" Use for /correct\.", "",
         "slash trigger removed"),
        (r"^disable-model-invocation: true\n", "",
         "host-specific frontmatter key dropped"),
    ],
    "pstack/skills/sharpen/SKILL.md": [
        (r"^description: .*$",
         'description: "Rewrite a task that is too shallow rather than too big: '
         'name what a top practitioner would add, the raw material to start '
         'from, the tools, and the outside evidence that proves the result. Use '
         'when the user asks to deepen a task or rewrite a prompt."',
         "description rewritten to state when to use it"),
        (r"^disable-model-invocation: true\n", "",
         "host-specific frontmatter key dropped"),
    ],
    "pstack/skills/statechart/SKILL.md": [
        (r"Use for /statechart, or to show a bug as a path through states\.",
         "Use when a state machine's rules need checking, or to show a bug as a "
         "path through states.",
         "slash trigger rewritten as a condition"),
        (r"^disable-model-invocation: true\n", "",
         "host-specific frontmatter key dropped"),
    ],
    "pstack/skills/typescript-best-practices/SKILL.md": [
        (r'^paths: \["\*\*/\*\.ts", "\*\*/\*\.tsx"\]\n', "",
         "host-specific frontmatter key dropped"),
        (r"^disable-model-invocation: true\n", "",
         "host-specific frontmatter key dropped"),
        (r"Apply the \*\*type-system-discipline\*\* principle skill first\.",
         "Apply these rules before editing any `.ts` or `.tsx` file.",
         "sibling skill reference inlined"),
        (r"See the \*\*boundary-discipline\*\* principle skill\.",
         "Parse external data once, at the boundary, into a named domain type.",
         "sibling skill reference inlined"),
    ],
    "addyosmani/skills/constraint-driven-development/SKILL.md": [
        (r"^description: .*$",
         'description: "Establishes a project\'s quality bar as a written '
         'contract and stops agents quietly lowering it: it interviews the user '
         'on which dimensions matter, supplies sane default thresholds when they '
         'have no number in mind, records everything in CONSTRAINTS.md, and '
         'watches the diff for a weakened bar -- new @ts-ignore or '
         'eslint-disable suppressions, skipped or deleted tests, assertions '
         'stripped out, unimplemented stubs, thresholds edited down. Use when no '
         'quality bar is written down, when the user says 「set up constraints」 '
         'or 「define our standards」, or when an agent keeps '
         'silencing checks and skipping tests to get to green."',
         "truncated upstream description replaced"),
        (r"Other skills in this pack describe what good looks like\. "
         r"`code-review-and-quality` gives you five axes\. "
         r"`test-driven-development` gives you a cycle\. "
         r"`security-and-hardening` gives you a threat list\. "
         r"All of that lives in prose the agent reads and may or may not "
         r"follow, and none of it survives the end of the session\.",
         "Prose guidance describes what good looks like, but it lives only in "
         "what the agent happens to read, and none of it survives the end of "
         "the session.",
         "pack cross-reference removed"),
        (r"Follow the one-question-at-a-time discipline from `interview-me`, "
         r"with one change: every question here has a default, so \"I don't "
         r"know\" is a complete answer that still produces a working config\.",
         "Ask one question at a time, and give every question a default: \"I "
         "don't know\" must still produce a working config.",
         "sibling skill reference inlined"),
        (r"\| Agent harness \| `\.claude/`, `\.codex/`, `AGENTS\.md` \|",
         "| Agent instructions | `AGENTS.md` and other agent-facing docs |",
         "foreign harness paths replaced"),
        (r"Then add one line to `AGENTS\.md` and `CLAUDE\.md`:",
         "Then add one line to the project's agent instruction file "
         "(`AGENTS.md`):",
         "`CLAUDE.md` reference removed"),
        (r"- \[ \] `AGENTS\.md` or `CLAUDE\.md` points at the file",
         "- [ ] `AGENTS.md` points at the file",
         "`CLAUDE.md` reference removed"),
        (r"- The user wants a code review right now \(`code-review-and-quality`\) "
         r"or a CI pipeline built \(`ci-cd-and-automation`\)",
         "- The user wants a code review right now, or a CI pipeline built",
         "pack cross-reference removed"),
        (r"\n## See Also\n\n(?:- [^\n]*\n)+",
         "\n",
         "See Also section dropped (every entry is pack-internal)"),
        (r"\(CI, `/loop`, autonomous runs\)",
         "(CI, autonomous runs)",
         "slash-command mention dropped, sentence kept"),
        (r"\| Phase \| Command \| What runs \| Budget \|\n"
         r"\|-+\|-+\|-+\|-+\|\n"
         r"\| BUILD \| `/build` \| Types, lint, secrets, the floor \|[^\n]*\n"
         r"\| VERIFY \| `/test` \| Related tests, coverage on changed lines \|[^\n]*\n"
         r"\| REVIEW \| `/review` \| Everything, plus the guards below \|[^\n]*\n"
         r"\| SHIP \| `/ship` \| Direction checks, no regressions \|[^\n]*",
         "| Phase | What runs | Budget |\n"
         "|-------|-----------|--------|\n"
         "| BUILD | Types, lint, secrets, the floor | under 5s, changed file only |\n"
         "| VERIFY | Related tests, coverage on changed lines | under 90s |\n"
         "| REVIEW | Everything, plus the guards below | minutes |\n"
         "| SHIP | Direction checks, no regressions | CI |",
         "phase table keeps its phases, drops the command column"),
        (r"axe-core encodes WCAG, `osv-scanner` reads a vulnerability database",
         "axe-core encodes WCAG, osv-scanner reads a vulnerability database",
         "tool name unbackticked: it is not an asset id"),
    ],
    # --- qa-skills -----------------------------------------------------
    # Bulk rewrites live in SOURCE_RULES; the rules below run afterwards and
    # therefore match text that already carries `skill://<prefix>core/` URIs.
    "qa-skills/skills/core/SKILL.md": [
        (r"本目录是框架的公共层：[\s\S]*?单一维护源，多 skill 复用。",
         "本 skill 是 QA 套件的公共层：不定义工作流、不面向用户触发，只被其余 "
         "12 个 QA skill 按需读取。本 fork 把它作为独立技能分发，共享文档用 "
         "`skill://" + refscan.RUNTIME_PREFIX + "core/<file>` 引用，单一维护源、多 skill 复用。",
         "core 目录说明改写为独立技能说明"),
    ],
    "qa-skills/skills/core/evidence.md": [
        (r"^> 本文件位于 `skill://" + r"[^`]+` 共享引用层（[^）]*）。$",
         "> 本文件位于 `skill://" + refscan.RUNTIME_PREFIX + "core` 共享知识库"
         "（该技能只作依赖单元存在，正文不独立触发）。",
         "core location note rewritten for the skill layout"),
    ],
    "qa-skills/skills/core/schema-extraction.md": [
        (r"（无第三方依赖，路径相对消费本文件的 SKILL\.md 所在目录）",
         "（无第三方依赖；脚本随本 skill 的 scripts 目录分发）",
         "相对路径说明改写为技能内脚本说明"),
    ],
    "qa-skills/skills/core/test-type-matrix.md": [
        (r"（路径相对 test-strategy 的 SKILL\.md 所在目录）",
         "（脚本随 " + refscan.RUNTIME_PREFIX + "core 技能分发）",
         "相对路径说明改写为技能内脚本说明"),
    ],
    "qa-skills/skills/automated-e2e-testing/references/helpers_reference.md": [
        (r"^> \*\*路径口径\*\*：.*$",
         "> **路径口径**：`skill://` 开头的是可直接 read 的技能 URI；"
         "`references/...` 等其余相对路径按本 skill 目录解析。",
         "path-convention note rewritten for the skill URI layout"),
    ],
    "qa-skills/skills/automated-e2e-testing/references/playwright-conventions.md": [
        (r"^> \*\*路径口径\*\*：.*$",
         "> **路径口径**：`skill://` 开头的是可直接 read 的技能 URI；"
         "`references/...` 等其余相对路径按本 skill 目录解析。",
         "path-convention note rewritten for the skill URI layout"),
    ],
    "qa-skills/skills/test-case-writing/templates/markmap_template.md": [
        (r"^> \*\*路径口径\*\*：.*$",
         "> **路径口径**：`skill://` 开头的是可直接 read 的技能 URI；"
         "其余相对路径按本 skill 目录解析。",
         "path-convention note rewritten for the skill URI layout"),
    ],
    "qa-skills/skills/qa-memory/SKILL.md": [
        (r"宿主的记忆机制（CLAUDE\.md / auto-memory 等）",
         "宿主的记忆机制（AGENTS.md / 宿主记忆等）",
         "`CLAUDE.md` reference removed"),
        (r"- 项目只有 CLAUDE\.md 无 AGENTS\.md → CLAUDE\.md 加 `@\.qa/INDEX\.md`",
         "- 项目只有 AGENTS.md（或同类常驻指令文件）→ 在其中追加 `@.qa/INDEX.md`",
         "`CLAUDE.md` reference removed"),
    ],
    "qa-skills/skills/core/pipeline-integration.md": [
        (r"claude -p \"", "omp -p \"", "headless CLI invocation switched to omp"),
        (r"--allowedTools \"Bash,Read,Write,Glob,Grep\"",
         "--tools=bash,read,write,glob,grep",
         "Claude tool allowlist switched to omp tool names"),
        (r"# claude 非零退出码", "# omp 非零退出码",
         "exit-code comment switched to omp"),
        (r"# 切勿写成 \"--dangerously-skip-permissions \|\| EXIT=\$\?\"",
         "# 切勿写成 \"--auto-approve || EXIT=$?\"",
         "anti-pattern comment switched to omp flags"),
        (r"\n {12}--dangerously-skip-permissions\n", "\n            --auto-approve\n",
         "permission flag switched to omp"),
    ],
}


class Drift(Exception):
    """An upstream sentence the rule targets is gone or duplicated."""


# Keys are source slugs.  `{prefix}` expands to the runtime name prefix.
SOURCE_RULES = {
    "qa-skills": [
        # a shared script is executed, so it needs a directory rather than a
        # URI; `<xxx-skill>` is the placeholder idiom ECC itself uses
        (r"python3 \.\./core/scripts/", "python3 <{prefix}core-skill>/scripts/",
         "core script call rewritten to the skill-dir placeholder", 5),
        # everything else under core/ is read, so a skill URI is what to follow
        (r"\.\./core/", "skill://{prefix}core/",
         "core shared-file reference rewritten to a skill URI", 141),
        # single-word names never match the bare-name rule in refscan
        (r"`qa`", "`skill://{prefix}qa`",
         "bare `qa` rewritten to a skill URI", 19),
        (r"`core`", "`skill://{prefix}core`",
         "bare `core` rewritten to a skill URI", 1),
        (r"`core/methods/`", "`skill://{prefix}core/methods/`",
         "core methods reference rewritten to a skill URI", 1),
        (r"`core/`", "`skill://{prefix}core`",
         "core directory reference rewritten to a skill URI", 5),
        # marketplace-only frontmatter; omp reads name and description alone
        (r"^slug: .*\n", "", "marketplace-only slug dropped", 13),
        (r"^displayName: .*\n", "", "marketplace-only displayName dropped", 13),
    ],
}

# Per-source hit totals accumulated by apply_rules and checked by
# sync_absorbed.py once the whole tree has been rewritten.
SOURCE_COUNTS = {}


def reset_source_counts():
    SOURCE_COUNTS.clear()


def apply_rules(key, text):
    """Run the rules for `key`; return (text, notes). Raises Drift."""
    notes = []
    source = key.split("/", 1)[0]
    for find, replace, note, _expected in SOURCE_RULES.get(source, ()):
        pattern = re.compile(find, flags=re.MULTILINE)
        text, hits = pattern.subn(
            replace.format(prefix=refscan.RUNTIME_PREFIX), text)
        bucket = SOURCE_COUNTS.setdefault(source, {})
        bucket[note] = bucket.get(note, 0) + hits
    for find, replace, note in RULES.get(key, ()):
        pattern = re.compile(find, flags=re.MULTILINE)
        hits = pattern.findall(text)
        if len(hits) != 1:
            raise Drift(
                "%s: rule %r matched %d times (expected 1)"
                % (key, note, len(hits)))
        text = pattern.sub(lambda _m: replace, text, count=1)
        notes.append(note)
    return text, notes


def verify_source_counts():
    """Every source rule must have rewritten as many places as counted."""
    bad = []
    for source, rules in SOURCE_RULES.items():
        for _find, _replace, note, expected in rules:
            got = SOURCE_COUNTS.get(source, {}).get(note, 0)
            if got != expected:
                bad.append("%s: rule %r rewrote %d places, expected %d"
                           % (source, note, got, expected))
    if bad:
        raise Drift("\n".join(bad))
