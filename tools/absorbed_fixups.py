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
"""

import re

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
    ],
}


class Drift(Exception):
    """An upstream sentence the rule targets is gone or duplicated."""


def apply_rules(key, text):
    """Run the rules for `key`; return (text, notes). Raises Drift."""
    notes = []
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
