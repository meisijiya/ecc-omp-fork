#!/usr/bin/env python
"""Shared reference scanner and repairer for the fork's asset tree.

A "dangling reference" is a mention of a skill / agent / command / rule that
the model is expected to resolve, but which does not exist in the *currently
active profile* of this fork. The model reads such a line and then tries to
call a resource that is not there -> a failed tool call at best, a hallucinated
resource at worst.

Two consumers need the exact same answer, so the detection lives here once:

  tools/check_refs.py        the gate -- reports what is still dangling
  tools/apply_selection.py   the materializer -- removes those references while
                             upstream content is copied into the runtime tree

If the two used different heuristics, the gate would either stay red after a
repair or pass on text the model still cannot follow.

What is scanned
  skills/  commands/  agents/  rules/
                             materialized runtime assets of the active profile
  own/                          fork-authored sources (own/skills, own/rules, ...)

How a reference is recognized
  skill    `skill://name`, `skills/name/`, `skills/name/<file>`
  agent    `agent://name`, `agents/name.md`
  rule     `rule://name`, `rules/name.md`
  command  `/name`, `commands/name.md`
  link     a relative markdown link (`[text](../other/SKILL.md)`) -- resolved
           against the directory the document has in the runtime tree
  path     a path form (`skills/name/`, `agents/name.md`, `rules/name.md`)
           -- an asset named by its location in the plugin tree. The model
           cannot open such a path (the plugin lives outside the working
           directory), so it is rewritten to the canonical URI of the asset.
           A path form that names no asset of the active profile, or that
           points into a nested `rules/<dir>/` tree (omp discovers only
           flat `rules/<name>.md`), is a dangling reference.
  skill | agent
           a backticked bare name (`name`) that either
             * exists in pool/ (so it is a genuine upstream asset of this fork), or
             * sits in an explicit asset context: the line, the enclosing
               section or the enclosing markdown table mentions skill/agent/
               技能/代理 (a "rule" cue alone is NOT enough: upstream skills
               talk about coding rules all the time),
           and the name is kebab-case shaped (`a-b-c`). A single lowercase word
               (`tdd`, `council`) only counts inside an explicit asset list such
               as a "## Related Skills" section.

  A fenced code block shows literal text, not a pointer. Its lines are not
  judged at all -- that is what keeps the ADR index template (a table of
  example file names) intact.

How a relative link is judged
  The model reads the markdown source, and a relative path that leaves the
  skill directory cannot be followed at runtime. So a link is mapped onto the
  namespace omp can read:

    skills/<name>/...   -> skill://<name>[/<path inside the skill>]
    commands/<name>.md  -> /<name>
    agents/<name>.md    -> <name>
    rules/<name>.md     -> rule://<name>        (flat rules only)

  A link that maps to nothing readable (a nested `rules/react/hooks.md`, a
  `docs/` file, a skill outside the active profile) is dangling.

How it is judged
  A reference is OK when the name exists in the materialized set:
    skills/<name>/   commands/<name>.md   agents/<name>.md   rules/<name>.md
  Otherwise it is dangling, with the kind it was supposed to be (from the
  explicit URI prefix, else from the pool, else from the context).

  `pool/` is only used to *type* a dangling name and to recognize bare names as
  asset references at all; the verdict is always against the materialized set,
  because that is what the model can actually resolve.

How dangling references are repaired
  A pointer to an asset that is not shipped is worse than no pointer: the model
  either chases it or invents it. The repair therefore removes the pointer:

    * a relative link that resolves becomes the canonical URI
      (`[react-testing](../react-testing/SKILL.md)` -> `skill://react-testing`),
      because a relative path that leaves the skill directory cannot be
      followed at runtime,
    * a slash command that names the owning skill ("User types
      `/my-skill`") is the upstream spelling of "the user invokes this skill"
      -- it is rewritten to the skill URI instead of being cut,
    * if the line still references a resolvable asset, only the dangling token
      is cut out (together with the punctuation that belonged to it),
    * otherwise the whole line is dropped -- a line whose only job was to point
      at a missing asset has nothing left to say,
    * a heading whose section lost all of its content goes with it -- a title
      with nothing under it says less than no title at all. A heading that
      was empty in the source stays: upstream ships such sections on purpose.

  The repair is applied at materialization time against the *resolved* profile,
  so a reference to an asset that another profile does ship is kept there and
  removed only in the profile that lacks it.

Known limitations
  * This is a regex heuristic, not an AST-level parser. It will produce false
    positives (e.g. a `/token` that is really a URL path or an HTTP endpoint)
    and false negatives (a reference written in prose without backticks, in a
    nested path such as `rules/react/testing.md`).
  * Only the flat `rules/<name>.md` / `skills/<name>/` forms are resolved;
    a nested rules path is treated as unreadable, not as readable.
  * Lines inside a fenced code block are not judged, so a pointer written in
    an example block is not reported.
  * `own/patches/` is scanned like any other markdown file. A patched asset is
    materialized from there, so a dangling reference in a patch shows up twice
    (once in the patch, once in the materialized file). That is intended: both
    copies have to be fixed.
"""

import json
import os
import posixpath
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ("skills", "commands", "agents", "rules", "own")
KINDS = ("skills", "commands", "agents", "rules")

# --- reference syntax ------------------------------------------------------

RE_SKILL_URI = re.compile(r"skill://([A-Za-z0-9][A-Za-z0-9._-]*)")
RE_AGENT_URI = re.compile(r"agent://([A-Za-z0-9][A-Za-z0-9._-]*)")
RE_RULE_URI = re.compile(r"rule://([A-Za-z0-9][A-Za-z0-9._-]*)")
# Path forms name an asset by its location in the plugin tree:
#   skills/<name>/            a skill directory
#   skills/<name>/<file>      a file inside a skill
#   commands/<name>.md        a command
#   agents/<name>.md          an agent
#   rules/<name>.md           a flat rule (the only shape omp discovers)
#   rules/<dir>/<file>.md     a nested rule -- never discoverable at runtime
RE_SKILL_PATH = re.compile(
    r"(?<![\w./\\-])skills/[A-Za-z0-9][A-Za-z0-9._-]*"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*/?")
RE_FLAT_PATH = re.compile(
    r"(?<![\w./\\-])(?:commands|agents|rules)/[A-Za-z0-9][A-Za-z0-9._-]*\.md")
RE_NESTED_RULE_PATH = re.compile(
    r"(?<![\w./\\])rules/[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\.md")
# The nested rule shape is matched first: it is a superset of the flat rule
# shape and the two would otherwise both match the same text.
PATH_FORMS = (RE_NESTED_RULE_PATH, RE_FLAT_PATH, RE_SKILL_PATH)
RE_CMD_BACK = re.compile(r"`(/[a-z][a-z0-9]*(?:-[a-z0-9]+)*)`")
RE_CMD_INLINE = re.compile(r"(?<![\w`<>/.:\\-])(/[a-z][a-z0-9]*(?:-[a-z0-9]+)*)(?![\w/.\\-])")
RE_BARE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9._-]*)`")
# A reference that names its kind inline. Upstream writes it in two shapes:
# the whole token inside one pair of backticks ("`skill: foo`") and the
# prefix outside with the name in its own pair ("skill: `foo`"). The
# bare-name rule needs a plain name between the backticks, so the first
# shape never reaches it; it also skips names that contain a slash, so the
# nested paths of the second shape never reach it either. These two rules
# are the only ones that can see the kind.
RE_PREFIXED_WHOLE = re.compile(
    r"`(?P<kind>skills?|agents?|rules?|commands?)\s*:\s*"
    r"(?P<name>[A-Za-z0-9][A-Za-z0-9._/-]*)`")
RE_PREFIXED_OUTER = re.compile(
    r"(?<![\w`.-])(?P<kind>skills?|agents?|rules?|commands?)\s*:\s*"
    r"`(?P<name>[A-Za-z0-9][A-Za-z0-9._/-]*)`")
# The rest of a list that shares one prefix: "rules: `a`, `b`, `c`".
RE_PREFIXED_TAIL = re.compile(r",\s*`(?P<name>[A-Za-z0-9][A-Za-z0-9._/-]*)`")
# The plugin-tree roots that the path rules own. A prefixed reference that
# starts with one of them is a path form in disguise and is left to them.
PATH_ROOTS = ("skills/", "commands/", "agents/", "rules/")

# How this fork addresses each kind at runtime, for a kind-qualified name.
PREFIXED_KIND_KEY = {
    "skill": "skills", "agent": "agents",
    "rule": "rules", "command": "commands",
}
PREFIXED_CANONICAL = {
    "skills": lambda n: "skill://" + n,
    "rules": lambda n: "rule://" + n,
    "commands": lambda n: "/" + n,
    # an agent has no readable URI: omp dispatches agents by bare name
    "agents": lambda n: n,
}

# A bare name only counts as an asset reference if it looks like an asset id.
RE_ASSET_SHAPE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
# Single lowercase words (e.g. `tdd`, `council`) are accepted only inside an
# explicit asset context, never in free prose.
RE_SINGLE_WORD = re.compile(r"^[a-z][a-z0-9]{2,}$")

# A markdown link to a file: [text](target). Only relative targets are
# interesting here: an absolute URL leaves the plugin and cannot be checked.
RE_MD_LINK = re.compile(r"\[([^\]\n]*)\]\(([^)\s]+)\)")
# Link targets that are not local paths.
RE_EXTERNAL_TARGET = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)

# --- context cues ----------------------------------------------------------

CUES = {
    "skill": re.compile(r"skill|技能", re.I),
    "agent": re.compile(r"\bagents?\b|代理|sub-?agent", re.I),
    "rule": re.compile(r"\brules?\b|规则", re.I),
    "command": re.compile(r"\bcommands?\b|命令", re.I),
}

# Only these cues turn a bare name into an asset reference. "rule" is not one
# of them: upstream skills talk a lot about coding *rules* ("### Rules",
# "Requirements, Rules, and Risks"), which has nothing to do with this fork's
# rule assets.
ENABLE_CUES = ("skill", "agent")

# A heading that introduces an explicit list of assets, e.g. "## Related
# Skills". Single-word names are only accepted under such a heading.
STRONG_LIST_HEADING = re.compile(r"related\s+skills|^#+\s*skills?\b|^#+\s*技能", re.I)
BULLET = re.compile(r"^\s*[-*]\s")

# Lowercase words that show up in backticks but never denote an asset.
STOP_WORDS = {
    "read", "write", "edit", "bash", "grep", "glob", "task", "todo",
    "ask", "multi-edit", "skill", "agent", "rule", "command",
}
# Cue words that make an inline `/token` look like a command invocation.
CMD_CUE = re.compile(r"\b(run|runs|running|command|commands|execute|executes)\b|命令", re.I)

# Path segments / HTTP endpoints / web routes that look like `/token` but are
# not commands. Only consulted for tokens that are not in the pool.
PATH_NOISE = {
    "tmp", "temp", "var", "usr", "etc", "home", "opt", "root", "workspace",
    "mnt", "media", "proc", "sys", "dev", "bin", "sbin", "lib", "local",
    "build", "dist", "src", "test", "tests", "docs", "public", "static",
    "health", "ready", "live", "livez", "readyz", "healthz", "metrics",
    "status", "api", "app", "apps", "user", "users", "items", "item",
    "admin", "login", "logout", "me", "id", "version", "info", "help",
    "data", "server", "style", "script", "scripts", "comments", "reviews",
    "goal", "goals", "phase", "executions", "execution", "mapper",
    "association", "foreach", "where", "foo", "something", "saved",
    "domain", "main", "plugin", "requirements", "markets", "utils",
    "template", "token", "creator-dashboard", "docker-entrypoint-initdb",
    "code", "button", "form", "select", "span", "div", "li", "ul", "if",
    "p", "s", "g", "x",
}


# ---------------------------------------------------------------------------
# Manifest / tree inspection
# ---------------------------------------------------------------------------

def load_json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def scan_files(dirs=None):
    """Every markdown file under the scanned directories, in a stable order."""
    out = []
    for d in (dirs if dirs is not None else SCAN_DIRS):
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    out.append(os.path.join(dirpath, fn))
    return out


def materialized_sets():
    """{kind: set(names)} for what is actually on disk right now."""
    out = {}
    for kind in KINDS:
        d = os.path.join(ROOT, kind)
        names = set()
        if os.path.isdir(d):
            for n in os.listdir(d):
                p = os.path.join(d, n)
                if kind == "skills":
                    if os.path.isdir(p):
                        names.add(n)
                elif n.endswith(".md"):
                    names.add(os.path.splitext(n)[0])
        out[kind] = names
    return out


def pool_sets():
    """{kind: set(names)} for the upstream snapshot (typing / recognition only)."""
    out = {}
    for kind in ("skills", "commands", "agents"):
        d = os.path.join(ROOT, "pool", kind)
        names = set()
        if os.path.isdir(d):
            for n in os.listdir(d):
                p = os.path.join(d, n)
                if kind == "skills":
                    if os.path.isdir(p):
                        names.add(n)
                elif n.endswith(".md"):
                    names.add(os.path.splitext(n)[0])
        out[kind] = names
    return out


def external_refs():
    """Assets this fork does NOT ship but may legitimately point at.

    Some references in upstream content (and in the fork's own router skill)
    name a resource that lives in another omp plugin, e.g. the `code-review`
    skill of the mattpocock-skills plugin. Those references are real for the
    user, so the gate must not call them dangling -- but they must also be
    declared, so that "does the model resolve this?" stays an answerable
    question instead of an accident of what happens to be installed.

    Returns {kind: set(names)} read from manifest/external_refs.json.
    """
    path = os.path.join(ROOT, "manifest", "external_refs.json")
    if not os.path.isfile(path):
        return {kind: set() for kind in KINDS}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read manifest/external_refs.json: {exc}")
    out = {}
    for kind in KINDS:
        names = data.get(kind, [])
        if not isinstance(names, list):
            raise SystemExit(
                f"manifest/external_refs.json: {kind} must be a list of names"
            )
        out[kind] = set(names)
    return out


def pool_kind_of(pool=None):
    """Map an upstream asset name to its kind (skills win over commands)."""
    pool = pool if pool is not None else pool_sets()
    out = {}
    for kind, singular in (("skills", "skill"), ("commands", "command"),
                           ("agents", "agent")):
        for n in pool[kind]:
            out.setdefault(n, singular)
    return out


# --- relative link resolution ----------------------------------------------
#
# A markdown link inside a skill is written relative to the upstream repo
# layout ("../accessibility/SKILL.md", "../../rules/react/hooks.md"). The
# model reads a skill through `skill://<name>` and can follow `skill://<name>/
# <path>`; it cannot follow a path that leaves the skill. So a relative target
# is mapped onto the namespace the model can actually read:
#
#   skills/<name>/...   -> skill <name>      (plus a path inside that skill)
#   commands/<name>.md  -> command <name>
#   agents/<name>.md    -> agent <name>
#   rules/<name>.md     -> rule <name>      (flat only -- omp discovers flat
#                                             rule files)
#
# Anything else (a nested rules/ directory, a docs/ file) is not readable at
# runtime and is therefore a dangling pointer.

def resolve_link(base, target):
    """Resolve a relative link target against the runtime tree.

    `base` is the runtime directory that holds the link, e.g.
    "skills/react-patterns" or "commands". Returns a dict:

      kind      "skill" / "command" / "agent" / "rule", or None when the
                target does not point at a runtime namespace at all
      name      the asset name inside that namespace
      subpath   path inside the asset ("" for the asset itself)
      resolved  the normalized runtime path, for reporting
    """
    resolved = posixpath.normpath(posixpath.join(base, target))
    parts = resolved.split("/")
    info = {"kind": None, "name": "", "subpath": "", "resolved": resolved}
    if parts[0] == "skills" and len(parts) >= 2:
        info.update(kind="skill", name=parts[1], subpath="/".join(parts[2:]))
    elif parts[0] == "commands" and len(parts) == 2 and parts[1].endswith(".md"):
        info.update(kind="command", name=parts[1][:-3])
    elif parts[0] == "agents" and len(parts) == 2 and parts[1].endswith(".md"):
        info.update(kind="agent", name=parts[1][:-3])
    elif parts[0] == "rules" and len(parts) == 2 and parts[1].endswith(".md"):
        info.update(kind="rule", name=parts[1][:-3])
    return info


def runtime_exists(rel_path):
    """Does a runtime path exist in the materialized tree?"""
    return os.path.isfile(os.path.join(ROOT, *rel_path.split("/")))


# --- path forms ------------------------------------------------------------
#
# A path form names an asset by its location in the plugin tree:
# `skills/<name>/`, `skills/<name>/<file>`, `commands/<name>.md`,
# `agents/<name>.md`, `rules/<name>.md`. The model cannot follow such a
# path -- the plugin lives outside the working directory -- so the form is
# rewritten to the canonical URI of the asset it names. A path that names
# no asset of the active profile is a dangling reference like any other.

def classify_path_form(target, mat, exists):
    """Classify one path-form asset reference.

    `target` is the path text as written, e.g. "skills/react-testing/".
    Returns a dict with the asset kind, the name, whether it resolves in
    the active profile and the canonical way to address the asset (None
    when the path is the only way to name it, or when it resolves to
    nothing).
    """
    root, _, rest = target.partition("/")
    rest = rest.rstrip("/")
    if root == "skills":
        parts = [p for p in rest.split("/") if p]
        name = parts[0]
        subpath = "/".join(parts[1:])
        if name not in mat["skills"]:
            return {"kind": "skill", "name": name, "ok": False,
                    "reason": "skills/<name>/, no such skill in the active profile",
                    "canonical": None}
        if subpath and subpath != "SKILL.md" \
                and not exists("skills/" + name + "/" + subpath):
            return {"kind": "skill", "name": name, "ok": False,
                    "reason": "skills/<name>/<file>, the skill does not ship that file",
                    "canonical": None}
        canonical = "skill://" + name
        if subpath and subpath != "SKILL.md":
            canonical += "/" + subpath
        return {"kind": "skill", "name": name, "ok": True, "reason": "",
                "canonical": canonical}
    if root == "commands":
        name = rest[:-3] if rest.endswith(".md") else rest
        ok = name in mat["commands"]
        return {"kind": "command", "name": name, "ok": ok,
                "reason": "" if ok else
                "commands/<name>.md, no such command in the active profile",
                "canonical": ("/" + name) if ok else None}
    if root == "agents":
        # An agent definition has no readable URI: omp dispatches agents
        # by bare name. The path itself is the file's location inside the
        # plugin, which the model cannot open either -- so it is checked
        # for existence and otherwise kept as written.
        name = rest[:-3] if rest.endswith(".md") else rest
        ok = name in mat["agents"]
        return {"kind": "agent", "name": name, "ok": ok,
                "reason": "" if ok else
                "agents/<name>.md, no such agent in the active profile",
                "canonical": None}
    # rules
    parts = [p for p in rest.split("/") if p]
    if len(parts) > 1:
        return {"kind": "rule", "name": "/".join(parts), "ok": False,
                "reason": ("nested rules path; only flat rules/<name>.md is "
                           "discoverable at runtime"),
                "canonical": None}
    name = parts[0][:-3] if parts[0].endswith(".md") else parts[0]
    ok = name in mat["rules"]
    return {"kind": "rule", "name": name, "ok": ok,
            "reason": "" if ok else
            "rules/<name>.md, no such rule in the active profile",
            "canonical": ("rule://" + name) if ok else None}


# --- relative markdown links ----------------------------------------------

# A fenced code block shows literal text, not a pointer. Links inside it are
# examples (e.g. the ADR index template) and must not be touched.
RE_FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def fenced_lines(lines):
    """Indices of the lines that sit inside a fenced code block."""
    inside = set()
    fence = None
    for i, raw in enumerate(lines):
        m = RE_FENCE.match(raw)
        if fence is None:
            if m:
                fence = m.group(1)
                inside.add(i)
        else:
            inside.add(i)
            if m and m.group(1) == fence:
                fence = None
    return inside


def classify_link(base, target, mat, exists):
    """Classify one relative markdown link target.

    Returns None for targets that are not local (http:, mailto:, #anchor,
    absolute paths). Otherwise a dict with the asset kind, the name, whether
    it resolves in the active profile and the canonical URI the model can
    actually follow.
    """
    if RE_EXTERNAL_TARGET.match(target) or target.startswith("/"):
        return None
    info = resolve_link(base, target)
    kind = info["kind"]
    name = info["name"]
    subpath = info["subpath"]
    if kind is None:
        reason = "link points at a file this plugin does not ship"
        if info["resolved"].startswith("rules/"):
            reason = ("link points at a nested rules path; only flat "
                      "rules/<name>.md is readable")
        elif info["resolved"].startswith("docs/"):
            reason = "link points at a docs file this plugin does not ship"
        return {"kind": "file", "name": info["resolved"], "subpath": "",
                "ok": False, "reason": reason, "canonical": None}
    if kind == "skill":
        if name not in mat["skills"]:
            return {"kind": "skill", "name": name, "subpath": subpath,
                    "ok": False,
                    "reason": "link points at a skill outside the active profile",
                    "canonical": None}
        if subpath and subpath != "SKILL.md" \
                and not exists("skills/" + name + "/" + subpath):
            return {"kind": "skill", "name": name, "subpath": subpath,
                    "ok": False,
                    "reason": "link points at a file the skill does not ship",
                    "canonical": None}
        canonical = "skill://" + name
        if subpath and subpath != "SKILL.md":
            canonical += "/" + subpath
        return {"kind": "skill", "name": name, "subpath": subpath, "ok": True,
                "reason": "", "canonical": canonical}
    if kind == "command":
        ok = name in mat["commands"]
        return {"kind": "command", "name": name, "subpath": "", "ok": ok,
                "reason": "" if ok else
                "link points at a command outside the active profile",
                "canonical": "/" + name}
    if kind == "agent":
        ok = name in mat["agents"]
        return {"kind": "agent", "name": name, "subpath": "", "ok": ok,
                "reason": "" if ok else
                "link points at an agent outside the active profile",
                "canonical": name}
    ok = name in mat["rules"]
    return {"kind": "rule", "name": name, "subpath": "", "ok": ok,
            "reason": "" if ok else
            "link points at a rule outside the active profile",
            "canonical": "rule://" + name}


def source_exists(rel_path):
    """Does a runtime path exist in the tree the materializer copies from?

    The runtime tree is built from three sources: the upstream pool, the
    fork's own skills and the fork's full replacements. A skill ships all of
    its files, so a file inside a skill exists iff it exists in that skill's
    source directory.
    """
    parts = rel_path.split("/")
    if parts[0] != "skills" or len(parts) < 2:
        return False
    name = parts[1]
    rest = parts[2:]
    # a fork replacement wins over the upstream snapshot, and the fork's own
    # skills win over both -- exactly the order the materializer copies in
    for base in (os.path.join(ROOT, "own", "patches", "skills", name),
                 os.path.join(ROOT, "own", "skills", name),
                 os.path.join(ROOT, "pool", "skills", name)):
        if not os.path.isdir(base):
            continue
        if not rest:
            return True
        if os.path.isfile(os.path.join(base, *rest)):
            return True
        # this source is the one that will be copied -- a file it does not
        # have will not be in the runtime tree
        return False
    return False


def runtime_path(rel_path):
    """Map a repository path to the path it has in the runtime tree.

    own/skills/<n>/... and own/patches/skills/<n>/... are materialized as
    skills/<n>/..., own/rules/<n>.md as rules/<n>.md, and so on. Everything
    else keeps its path.
    """
    parts = rel_path.split("/")
    if parts[0] == "own":
        parts = parts[1:]
        if parts and parts[0] == "patches":
            parts = parts[1:]
        return "/".join(parts)
    return "/".join(parts)


def link_context(rel_path, exists=None):
    """Build the context needed to resolve relative links inside a file.

    `rel_path` is the repository path of the file; `exists` is a predicate
    that answers whether a runtime path (e.g. "skills/react-patterns/
    references/cli.md") is present in the tree.
    """
    rt = runtime_path(rel_path)
    parts = rt.split("/")
    if parts[0] == "skills" and len(parts) >= 2:
        owner_kind, owner = "skill", parts[1]
        sub = "/".join(parts[2:])
        base = "skills/" + owner
        if "/" in sub:
            base += "/" + sub.rsplit("/", 1)[0]
    elif parts[0] in ("commands", "agents", "rules") and len(parts) == 2:
        owner_kind = {"commands": "command", "agents": "agent",
                      "rules": "rule"}[parts[0]]
        owner = parts[1][:-3]
        base = parts[0]
    else:
        return None
    return {"base": base, "owner_kind": owner_kind, "owner": owner,
            "exists": exists}



def active_profile():
    try:
        selection = load_json("manifest", "selection.json")
    except OSError as exc:
        raise SystemExit(f"cannot read manifest/selection.json: {exc}")
    name = selection.get("active_profile")
    if not name:
        raise SystemExit("manifest/selection.json has no 'active_profile' field")
    path = os.path.join(ROOT, "manifest", "profiles", name + ".json")
    if not os.path.isfile(path):
        raise SystemExit(f"unknown active profile {name!r}: {path} not found")
    return name


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def table_header_cells(lines, idx):
    """Return the header cells of the markdown table starting at lines[idx]."""
    if idx + 1 >= len(lines):
        return None
    sep = lines[idx + 1].strip()
    if not sep.startswith("|"):
        return None
    if not re.fullmatch(r"\|[\s:|-]+\|?", sep):
        return None
    return [c.strip().lower() for c in lines[idx].strip().strip("|").split("|")]


def context_cues(text):
    """Return the set of asset kinds mentioned by a piece of context."""
    found = set()
    for kind, pat in CUES.items():
        if pat.search(text):
            found.add(kind)
    return found


class _Context:
    """Tracks the markdown structure a line lives in."""

    def __init__(self):
        self.heading = ""
        self.table_cue = set()
        self.in_table = False
        self.strong_list = False

    def update(self, lines, idx):
        """Advance the context to line `idx` (0-based) and return its cues."""
        raw = lines[idx]
        stripped = raw.strip()
        if stripped.startswith("#"):
            self.heading = stripped
            self.in_table = False
            self.strong_list = bool(STRONG_LIST_HEADING.search(stripped))
        elif stripped.startswith("|"):
            if not self.in_table:
                cells = table_header_cells(lines, idx)
                if cells is not None:
                    self.table_cue = context_cues(" ".join(cells))
                    self.in_table = True
        else:
            self.in_table = False
            self.table_cue = set()

        line_cues = context_cues(raw)
        section_cues = context_cues(self.heading) if self.heading else set()
        if self.table_cue:
            section_cues = section_cues | self.table_cue
        return line_cues, section_cues


def prefixed_refs(line):
    """Yield the kind-qualified references that no other rule owns.

    Upstream writes "skill: foo" in two shapes: the whole token inside one
    pair of backticks ("`skill: foo`") and the prefix outside with the name
    inside its own pair ("skill: `foo`"). The plain-name rule owns the
    second shape whenever the name is a plain asset name, and the command
    and path rules own it when the name is a command ("`/plan`") or a
    plugin-tree path ("skills/react-testing/").

    What is left for this rule is what nobody else can see:

    * the whole token in one pair of backticks -- the plain-name rule needs
      a plain name between them, so it never matches this shape;
    * a name that contains a slash or a dot -- the plain-name rule skips
      those names, so a nested path written this way ("rules:
      `ruby/coding-style`") would escape every other rule.

    Yields dicts with:
      kind   -- the singular kind the prefix names ("skill", "agent", ...)
      name   -- the asset name the prefix points at
      start/end -- the span of text the reference occupies
      whole  -- True when the prefix and the name share one pair of
                 backticks ("`skill: foo`")
    """
    out = []
    for m in RE_PREFIXED_WHOLE.finditer(line):
        name = m.group("name").strip()
        if name.startswith("/"):
            continue  # a slash command: the command rule owns it
        if name.startswith(PATH_ROOTS):
            continue  # a plugin-tree path: the path rules own it
        out.append({
            "kind": m.group("kind").rstrip("s"), "name": name,
            "start": m.start("kind"), "end": m.end("name"), "whole": True,
        })

    for m in RE_PREFIXED_OUTER.finditer(line):
        name = m.group("name").strip()
        if name.startswith("/"):
            continue  # a slash command: the command rule owns it
        if name.startswith(PATH_ROOTS):
            continue  # a plugin-tree path: the path rules own it
        if "/" not in name and "." not in name:
            continue  # a plain name: the plain-name rule owns it
        # the rest of the list shares the prefix: "rules: `a`, `b`"
        end = m.end()
        for c in RE_PREFIXED_TAIL.finditer(line, end):
            tail = c.group("name").strip()
            if "/" not in tail and "." not in tail:
                break
            if tail.startswith("/") or tail.startswith(PATH_ROOTS):
                break
            end = c.end()
        out.append({
            "kind": m.group("kind").rstrip("s"), "name": name,
            "start": m.start("kind"), "end": end, "whole": False,
        })
    return out


def scan_text(text, mat, pool, pool_kind_of, external=None,
              link_base=None, link_exists=None):
    """Scan a document; returns one record per reference found.

    Each record: line (1-based), name, kind, ok (bool), reason, start, end.
    `start`/`end` are offsets inside the line, so a repair can cut exactly the
    token that is dangling.

    `external` names assets that live in another omp plugin. A reference to
    one of them resolves for the user, so it is not reported as dangling.

    `link_base` is the runtime directory that holds the document. When it is
    given, relative markdown links are resolved against it and checked the
    same way; `link_exists` answers whether a file inside a skill is shipped.
    """
    external = external if external is not None else external_refs()

    def resolves(kind, name):
        return name in mat[kind] or name in external[kind]

    lines = text.split("\n")
    ctx = _Context()
    records = []

    def add(idx, name, kind, ok, reason, m, canonical=None, link=False,
            path_form=False, prefixed=False, wrap=False, start=None,
            end=None):
        records.append({
            "line": idx + 1,
            "name": name,
            "kind": kind,
            "ok": ok,
            "reason": reason,
            "start": m.start() if start is None else start,
            "end": m.end() if end is None else end,
            "canonical": canonical,
            "link": link,
            "path_form": path_form,
            "prefixed": prefixed,
            "wrap": wrap,
        })

    fenced = fenced_lines(lines)

    for idx, raw in enumerate(lines):
        # A fenced code block shows literal text, not a pointer. Nothing
        # inside it is a reference the model is expected to resolve, so the
        # whole line is skipped -- the heading context is not advanced either
        # (a "#" inside a fence is a comment, not a heading).
        if idx in fenced:
            continue

        line_cues, section_cues = ctx.update(lines, idx)

        # --- relative markdown links ----------------------------------------
        # A link is a pointer the model has to follow. It is only usable if it
        # resolves to an asset of the active profile; a relative path that
        # leaves the skill directory cannot be followed at runtime, so the
        # link is resolved against the runtime tree and rewritten to the
        # canonical URI.
        link_spans = []
        if link_base is not None:
            for m in RE_MD_LINK.finditer(raw):
                target = m.group(2)
                if RE_EXTERNAL_TARGET.match(target) or target.startswith("/"):
                    continue
                info = classify_link(link_base, target, mat,
                                     link_exists or runtime_exists)
                if info is None:
                    continue
                link_spans.append((m.start(), m.end()))
                add(idx, info["name"], info["kind"], info["ok"],
                    info["reason"], m, canonical=info["canonical"], link=True)

        def in_link(pos):
            return any(s <= pos < e for s, e in link_spans)

        # Every markdown link, classified or not. A path form inside link
        # text ("[skills/react-testing](../react-testing/SKILL.md)") is part
        # of that link, not a separate reference.
        all_link_spans = [(m.start(), m.end()) for m in RE_MD_LINK.finditer(raw)]

        def in_any_link(pos):
            return any(s <= pos < e for s, e in all_link_spans)

        # --- explicit URI references ---------------------------------------
        # a name inside a link we already classified is covered by that
        # classification -- do not report it twice
        for m in RE_SKILL_URI.finditer(raw):
            if in_link(m.start()):
                continue
            name = m.group(1)
            add(idx, name, "skill", resolves("skills", name),
                "skill:// reference, no such skill", m)
        # rule:// is the URI omp uses to read a rule. agent:// is not
        # checked: in omp it addresses the output of a sub-agent run, not
        # an asset of this plugin.
        for m in RE_RULE_URI.finditer(raw):
            if in_link(m.start()):
                continue
            name = m.group(1)
            add(idx, name, "rule", resolves("rules", name),
                "rule:// reference, no such rule", m)
        # --- kind-qualified references --------------------------------------
        # "skill: foo" names the kind inline. Upstream writes it in two
        # --- kind-qualified references ---------------------------------------
        # "skill: foo" names the kind inline. Two rules own the other
        # spellings, so only what they cannot see reaches this one: the
        # whole token inside one pair of backticks ("`skill: foo`") and a
        # name that carries a slash or a dot ("rules: `ruby/coding-style`").
        for ref in prefixed_refs(raw):
            if in_any_link(ref["start"]):
                continue
            kind = ref["kind"]
            plural = PREFIXED_KIND_KEY[kind]
            name = ref["name"]
            if name in mat.get(plural, ()):
                ok, reason = True, ""
            elif name in pool.get(plural, ()):
                ok = False
                reason = f"upstream {kind} not enabled in the active profile"
            elif "/" in name or "." in name:
                # a path that names no asset: a nested rules path cannot be
                # read at runtime, since the rules of this fork are flat
                ok = False
                reason = ("nested rules path; only flat rules/<name>.md is "
                          "discoverable at runtime") if kind == "rule" else \
                    f"no such {kind} in the active profile"
            else:
                # a plain word after the colon is prose, not a reference
                # ("command: npm", "rule: external")
                continue
            canonical = None
            if ok and ref["whole"]:
                # only the single-token shape can be rewritten: the span
                # covers the prefix and the name, the backticks stay
                canonical = PREFIXED_CANONICAL[plural](name)
            add(idx, name, kind, ok, reason, None, canonical=canonical,
                prefixed=True, wrap=ref["whole"], start=ref["start"],
                end=ref["end"])

        # --- path-form references -------------------------------------------
        # A path form names an asset by its location in the plugin tree
        # ("skills/react-testing/", "agents/planner.md"). The model cannot
        # follow such a path -- the plugin lives outside the working
        # directory -- so the form is rewritten to the canonical way to
        # address the asset. A path that names no asset of the active
        # profile is dangling like any other reference.
        for m in PATH_FORMS:
            for hit in m.finditer(raw):
                if in_any_link(hit.start()):
                    continue
                info = classify_path_form(hit.group(0), mat,
                                          link_exists or runtime_exists)
                add(idx, info["name"], info["kind"], info["ok"],
                    info["reason"], hit, canonical=info["canonical"],
                    path_form=True)

        # --- command references --------------------------------------------
        cmd_tokens = []
        for m in RE_CMD_BACK.finditer(raw):
            cmd_tokens.append((m, m.group(1)[1:], True))
        for m in RE_CMD_INLINE.finditer(raw):
            cmd_tokens.append((m, m.group(1)[1:], False))

        for m, name, backticked in cmd_tokens:
            if in_link(m.start()):
                continue
            if resolves("commands", name):
                add(idx, name, "command", True, "", m)
            elif name in pool["commands"]:
                add(idx, name, "command", False,
                    "command not enabled in the active profile", m)
            elif name in PATH_NOISE:
                continue
            elif backticked or CMD_CUE.search(raw):
                add(idx, name, "command", False,
                    "slash command, no such command in the active profile", m)

        # --- bare backticked names -----------------------------------------
        for m in RE_BARE.finditer(raw):
            if in_link(m.start()):
                continue
            name = m.group(1)
            if name.startswith("/"):
                continue
            if "." in name or "/" in name:
                continue  # file names, domains, paths
            if resolves("skills", name) or resolves("agents", name) \
                    or resolves("commands", name) or resolves("rules", name):
                add(idx, name, pool_kind_of.get(name, "skill"), True, "", m)
                continue
            in_pool = pool_kind_of.get(name)
            if in_pool is None:
                cues = line_cues | section_cues
                if not (cues & set(ENABLE_CUES)):
                    continue
                if name in STOP_WORDS:
                    continue
                if RE_ASSET_SHAPE.match(name):
                    shape_ok = True
                elif RE_SINGLE_WORD.match(name) and ctx.strong_list \
                        and BULLET.match(raw):
                    # a single word is only an asset id inside an explicit
                    # "Related Skills" style list
                    shape_ok = True
                else:
                    shape_ok = False
                if not shape_ok:
                    continue
                kind = "skill|agent"
                for k in ENABLE_CUES:
                    if k in cues:
                        kind = k
                        break
                add(idx, name, kind, False,
                    "named in an asset context, but no such asset in the "
                    "active profile", m)
            else:
                add(idx, name, in_pool, False,
                    f"upstream {in_pool} not enabled in the active profile", m)

    return records


def check_file(path, mat, pool, pool_kind_of, external=None):
    """Return the list of dangling references found in one file."""
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        # the tree is being re-materialized while we scan -> nothing to check
        return []
    except OSError as exc:
        raise SystemExit(f"cannot read {rel}: {exc}")

    ctx = link_context(rel)
    link_base = ctx["base"] if ctx else None

    findings = []
    for r in scan_text(text, mat, pool, pool_kind_of, external,
                       link_base=link_base, link_exists=runtime_exists):
        if r["ok"]:
            continue
        findings.append({
            "file": rel,
            "line": r["line"],
            "name": r["name"],
            "type": r["kind"],
            "reason": r["reason"],
        })
    return findings


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------

RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
RE_TRAILING_PAREN = re.compile(r"[ \t]*\([^()]*\)")
RE_MULTISPACE = re.compile(r"[ \t]{2,}")


def _link_span(line, start, end):
    """If the token sits inside a markdown link, return the whole link span."""
    open_bracket = line.rfind("[", 0, start)
    if open_bracket == -1:
        return None
    close_bracket = line.find("](", open_bracket)
    if close_bracket == -1 or close_bracket > start:
        return None
    close_paren = line.find(")", close_bracket + 2)
    if close_paren == -1 or close_paren < end:
        return None
    return open_bracket, close_paren + 1


def _cut_span(line, start, end):
    """Widen a token span so that everything that belonged to it goes too."""
    link = _link_span(line, start, end)
    if link is not None:
        return link

    # include the backticks around the token
    if start > 0 and line[start - 1] == "`" and end < len(line) and line[end] == "`":
        start -= 1
        end += 1

    # a short parenthetical right after the token describes that token
    m = RE_TRAILING_PAREN.match(line[end:])
    if m:
        end += m.end()

    # the separator that joined the token to the rest of the line
    if line[end:end + 2] == ", ":
        end += 2
    elif line[:start].endswith(", "):
        start -= 2
    elif line[end:end + 1] == ";":
        end += 1
    elif line[:start].endswith(";"):
        start -= 1

    return start, end


def _tidy(line):
    """Clean up the seams left behind by cutting a token out."""
    line = re.sub(r"\(\s*\)", "", line)
    line = re.sub(r",\s*,", ",", line)
    line = re.sub(r"[ \t]*:[ \t]*(?=\s*$)", "", line)
    line = RE_MULTISPACE.sub(" ", line)
    line = re.sub(r"[ \t]*,\s*$", "", line)
    line = re.sub(r"^\s*[-*]\s*$", "", line)
    return line


def _is_empty(line):
    stripped = re.sub(r"^[-*\s]+", "", line).strip()
    return not stripped.strip(" :;,.")


def _cut_entry(line, entry):
    """The span to remove for one dangling reference.

    A markdown link entry already spans the whole ``[text](target)``, so it is
    cut as it is and one separator is swallowed with it. Every other entry
    goes through ``_cut_span``, which already swallows the backticks, the
    explanatory parenthetical and the separator -- swallowing it twice would
    eat the comma of the neighbouring item and glue two backticks together.
    """
    if entry.get("link"):
        start, end = entry["start"], entry["end"]
        if line[end:end + 2] == ", ":
            end += 2
        elif line[:start].endswith(", "):
            start -= 2
        return start, end
    return _cut_span(line, entry["start"], entry["end"])


def _apply_edits(line, edits):
    """Apply (start, end, replacement) edits to a line, right to left."""
    out = line
    for start, end, repl in sorted(edits, key=lambda e: (e[0], e[1]),
                                   reverse=True):
        out = out[:start] + repl + out[end:]
    return out


# --- headings --------------------------------------------------------------

# An ATX heading is a run of "#" plus the space that separates it from the
# title. A "#" inside a fenced code block is a comment, not a heading, so
# the fence decides -- the same way it decides for references.
RE_HEADING = re.compile(r"^(#{1,6})\s")


def heading_levels(lines):
    """The level of every heading line, keyed by line index."""
    fenced = fenced_lines(lines)
    out = {}
    for i, raw in enumerate(lines):
        if i in fenced:
            continue
        m = RE_HEADING.match(raw)
        if m:
            out[i] = len(m.group(1))
    return out


def section_end(headings, idx, length):
    """Where the section of the heading at `idx` ends.

    A section runs up to the next heading of the same or a higher level. A
    deeper heading belongs to the section instead of ending it.
    """
    level = headings[idx]
    for j in range(idx + 1, length):
        if j in headings and headings[j] <= level:
            return j
    return length


def heading_title(line):
    """The title of a heading line, without the "#" run."""
    return RE_HEADING.sub("", line).strip()


def _source_has_content(lines, headings, idx):
    """Did the section of the heading at `idx` say anything in the source?

    A content line is a line that is neither empty nor a heading. A deeper
    heading counts as content of the section that holds it, because in the
    source every heading is still there.
    """
    for j in range(idx + 1, section_end(headings, idx, len(lines))):
        if j in headings or lines[j].strip():
            return True
    return False


def _repaired_has_content(lines, headings, idx, removed):
    """Does the section of the heading at `idx` still say anything?

    The same rule as in the source, applied to the repaired text: a deeper
    heading counts only while it is still there.
    """
    for j in range(idx + 1, section_end(headings, idx, len(lines))):
        if j in headings:
            if j not in removed:
                return True
        elif lines[j].strip():
            return True
    return False


def _empty_headings(source, repaired, kept):
    """The headings whose section the repair left without anything to say.

    `source` is the text before the repair, `repaired` the text after it and
    `kept` the source index of every line of `repaired`.

    A heading goes away when its section said something in the source and
    says nothing any more. A heading that was already empty in the source
    stays -- upstream ships such sections, and dropping them would change
    more than the repair was asked for.

    The verdicts cascade from the deepest heading upwards: a section that
    held nothing but a child heading loses that child as well and then has
    nothing left itself.
    """
    source_headings = heading_levels(source)
    repaired_headings = heading_levels(repaired)

    removed = set()
    while True:
        changed = False
        # deepest first: the fate of a child heading decides the fate of
        # the section that holds it
        for idx in sorted(repaired_headings,
                          key=lambda i: -repaired_headings[i]):
            if idx in removed:
                continue
            if _repaired_has_content(repaired, repaired_headings, idx,
                                      removed):
                continue
            if not _source_has_content(source, source_headings, kept[idx]):
                continue
            removed.add(idx)
            changed = True
        if not changed:
            return removed


def _remove_headings(repaired, removed):
    """Take the empty headings -- and the blank lines around them -- out.

    A section that lost its content is nothing but blank lines now, and
    they would leave holes in the text.
    """
    if not removed:
        return repaired
    headings = heading_levels(repaired)
    drop = set(removed)
    for idx in removed:
        for j in range(idx + 1, section_end(headings, idx, len(repaired))):
            if not repaired[j].strip():
                drop.add(j)
    return [repaired[i] for i in range(len(repaired)) if i not in drop]


def _trailing_newlines(lines):
    """How many newlines the text ends with."""
    n = 0
    while n < len(lines) and lines[len(lines) - 1 - n] == "":
        n += 1
    return n


def _same_ending(lines, want):
    """Give the text the ending the source had.

    Removing a heading at the end of a file takes the blank lines that
    followed it along, so the file could end with fewer newlines than it
    started with. The ending is part of the shape of the file, so it is put
    back.
    """
    have = _trailing_newlines(lines)
    if have == want:
        return lines
    if have > want:
        return lines[:len(lines) - (have - want)]
    if not lines:
        # the file lost its last line; it still ends the way the source did
        return [""] * (want + 1)
    return lines + [""] * (want - have)


def repair_text(text, mat, pool, pool_kind_of, owner=None, external=None,
                owner_kind="skill", link_base=None, link_exists=None):
    """Make every reference in a document followable.

    Three things happen here:

    * a relative markdown link that resolves becomes the canonical URI
      (``[react-testing](../react-testing/SKILL.md)`` ->
      ``skill://react-testing``). The model reads the markdown source, and a
      relative path that leaves the skill directory cannot be followed at
      runtime, so the link text is replaced by the URI that works.
    * a slash command that names the owner itself ("User types
      `/my-skill`") is the upstream spelling of "the user invokes this
      skill" -- it is rewritten to the skill URI instead of being cut.
    * a reference to an asset that does not exist in the materialized set is
      cut out. When the line exists only to point at that asset, the whole
      line goes.

    `owner` names the asset the text belongs to, `owner_kind` says whether
    that is a skill (only a skill may be addressed with `skill://`).
    `link_base` is the runtime directory of the document and `link_exists`
    answers whether a file inside a skill is shipped.

    Returns (new_text, notes) where notes describe what was changed.
    """
    records = scan_text(text, mat, pool, pool_kind_of, external,
                        link_base=link_base, link_exists=link_exists)
    if not records:
        return text, []

    lines = text.split("\n")
    source = lines[:]
    by_line = {}
    for r in records:
        by_line.setdefault(r["line"], []).append(r)

    notes = []
    drop = set()

    for line_no in sorted(by_line):
        entries = by_line[line_no]
        idx = line_no - 1
        line = lines[idx]

        # --- rewrites: self command, resolvable links, resolvable path forms
        edits = []
        for e in entries:
            if e["ok"]:
                if e.get("link") and e.get("canonical"):
                    edits.append((e["start"], e["end"],
                                  "`" + e["canonical"] + "`"))
                    notes.append({
                        "line": line_no, "name": e["name"],
                        "action": "rewrote link as " + e["canonical"],
                    })
                elif e.get("path_form") and e.get("canonical"):
                    edits.append((e["start"], e["end"], e["canonical"]))
                    notes.append({
                        "line": line_no, "name": e["name"],
                        "action": "rewrote path as " + e["canonical"],
                    })
                elif e.get("prefixed") and e.get("canonical"):
                    # "skill: foo" -> "skill://foo": the kind prefix is
                    # upstream's way of writing the URI the model can follow
                    edits.append((e["start"], e["end"], e["canonical"]))
                    notes.append({
                        "line": line_no, "name": e["name"],
                        "action": "rewrote prefixed reference as "
                                  + e["canonical"],
                    })
                continue
            if (e["kind"] == "command" and owner_kind == "skill" and owner
                    and e["name"] == owner and owner in mat["skills"]):
                edits.append((e["start"], e["end"], "skill://" + owner))
                notes.append({
                    "line": line_no, "name": e["name"],
                    "action": "rewrote self command as skill URI",
                })

        bad = [e for e in entries if not e["ok"]]
        # a self command that was rewritten is no longer dangling
        bad = [e for e in bad
               if not (e["kind"] == "command" and owner_kind == "skill"
                       and owner and e["name"] == owner
                       and owner in mat["skills"])]

        if bad:
            resolvable = [e for e in entries if e["ok"]]
            if not resolvable:
                # the whole line exists to point at an asset we do not ship
                drop.add(idx)
                for e in bad:
                    notes.append({
                        "line": line_no, "name": e["name"],
                        "action": "dropped line",
                    })
                continue

            # --- cut only the dangling tokens, keep the rest of the line
            spans = []
            for e in bad:
                spans.append(_cut_entry(line, e))
            spans.sort()
            merged = []
            for start, end in spans:
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            for start, end in merged:
                edits.append((start, end, ""))
            for e in bad:
                notes.append({
                    "line": line_no, "name": e["name"],
                    "action": "cut reference",
                })

        if not edits:
            continue
        out = _apply_edits(line, edits)
        out = _tidy(out)
        if _is_empty(out):
            drop.add(idx)
        else:
            lines[idx] = out

    # the lines that existed only to point at assets we do not ship are
    # gone; the survivors keep their place, so the section structure of the
    # source and of the result can still be lined up by index
    kept = [i for i in range(len(lines)) if i not in drop]
    repaired = [lines[i] for i in kept]

    # a heading whose section the repair emptied would leave a title
    # behind with nothing under it
    empty = _empty_headings(source, repaired, kept)
    if empty:
        for idx in sorted(empty):
            notes.append({
                "line": kept[idx] + 1,
                "name": heading_title(repaired[idx]),
                "action": "dropped heading",
            })
        repaired = _remove_headings(repaired, empty)
        repaired = _same_ending(repaired, _trailing_newlines(source))

    return "\n".join(repaired), notes
