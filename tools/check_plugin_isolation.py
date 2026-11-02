#!/usr/bin/env python3
"""Verify that omp-skill-forge's assets are served by omp only while the plugin is enabled.

The repo ships as an omp plugin. omp discovers a plugin's skills, commands,
rules and task agents by scanning the *enabled* plugin root, so disabling the
plugin must make all four surfaces disappear. This tool verifies that against a
real omp process rather than against the repository layout.

Attribution is content-based: an asset counts as "served by this plugin" only
when the text the runtime resolved for that name is the text in this repo.
The line the session prompt prints is not that text: omp shortens long skill
descriptions before it puts them in the prompt and caches the result in
`~/.omp/agent/skill-descriptions.db`, so a skill this repo ships is regularly
printed with a shorter description than its frontmatter carries. For skills
the resolved text comes from `omp skill list`; for the other kinds the prompt
line is the only view there is. Comparing the resolved text is what separates
our assets from a builtin of the same shape, so name collisions do not
produce false leaks. This fork's assets carry the `forge-` prefix, so the
builtin `security-reviewer` and our `forge-security-reviewer` no longer
share a name at all.

The expected asset set is read from the *installed* plugin root omp links this
fork from, because that directory is what omp actually scans. The tool also
compares that root against the repository tree file by file; any difference
means the installed plugin no longer matches the repository and the run fails.

Every probe carries the evidence that it was not blind: how many entries the
runtime advertised per surface, whether that surface existed at all, and
whether a user-level control skill outside this fork was still listed. A
runtime that lost the control skills, or that advertised fewer entries than
this repo ships while the plugin is enabled, is reported as an untrustworthy
probe instead of as a clean result -- "nothing is served" has to be measured,
not assumed.

Modes:
  --probe        read-only: report which fork assets the current omp runtime serves
  --toggle-test  disable the plugin, probe, re-enable, probe; prior state is always restored

Exit codes:
  0  probe consistent with the expected plugin state (shadowing is reported as a warning)
  1  inconsistency (assets leak while disabled, are missing while enabled, or the probe could not be trusted)
  2  tooling error (omp binary missing, RPC handshake failed, ...)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "omp-skill-forge"
KINDS = ("skills", "commands", "rules", "agents")
AGENT_DIR = Path.home() / ".omp" / "agent"


def control_skills(ours: dict[str, str]) -> list[str]:
    """User-level skills that do not come from this fork.

    They stay advertised whatever the plugin state is, so finding them proves
    the runtime probe really read the skill block. Without that control an
    empty block would look exactly like "the plugin serves nothing", and the
    disabled state could not be told apart from a broken probe.
    """
    skills_dir = AGENT_DIR / "skills"
    if not skills_dir.is_dir():
        return []
    names = sorted(
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    return [name for name in names if name not in ours]


# --------------------------------------------------------------------------- #
# repo side: frontmatter
# --------------------------------------------------------------------------- #
BLOCK_SCALAR_RE = re.compile(r"^[>|][+-]?\d*$")


def fold_block(block_lines: list[str]) -> str:
    """Fold a YAML block scalar into the single line omp advertises."""
    parts = [line.strip() for line in block_lines if line.strip()]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def frontmatter(path: Path) -> dict[str, str]:
    """Parse the `key: value` frontmatter of a markdown file.

    Block scalars (`description: >-` with indented continuation lines) are
    folded into one line; a plain parser would keep the `>-` marker and drop
    the text, which makes the repo description incomparable with the one the
    session prompt shows.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lines = text[3:end].splitlines()
    fields: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if BLOCK_SCALAR_RE.match(value):
            block_lines: list[str] = []
            while index < len(lines):
                nxt = lines[index]
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                block_lines.append(nxt)
                index += 1
            fields[key.strip()] = fold_block(block_lines)
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields


def repo_inventory(root: Path) -> dict[str, dict[str, str]]:
    """name -> {description} for every asset this repo ships."""
    inventory: dict[str, dict[str, str]] = {k: {} for k in KINDS}
    for skill_file in sorted((root / "skills").glob("*/SKILL.md")):
        fields = frontmatter(skill_file)
        name = fields.get("name") or skill_file.parent.name
        inventory["skills"][name] = fields.get("description", "")
    for command_file in sorted((root / "commands").glob("*.md")):
        fields = frontmatter(command_file)
        name = fields.get("name") or command_file.stem
        inventory["commands"][name] = fields.get("description", "")
    for agent_file in sorted((root / "agents").glob("*.md")):
        fields = frontmatter(agent_file)
        name = fields.get("name") or agent_file.stem
        inventory["agents"][name] = fields.get("description", "")
    for rule_file in sorted((root / "rules").glob("*.md")):
        fields = frontmatter(rule_file)
        name = fields.get("name") or rule_file.stem
        inventory["rules"][name] = fields.get("description", "")
    return inventory


# --------------------------------------------------------------------------- #
# runtime side: rpc
# --------------------------------------------------------------------------- #
def rpc_probe(omp_bin: str, cwd: str, timeout: int = 120) -> dict:
    """Start `omp --mode rpc`, ask for commands + session state, return raw data."""
    proc = subprocess.Popen(
        [omp_bin, "--mode", "rpc", "--no-ui", "--no-session", "--cwd", cwd],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdin is not None and proc.stdout is not None
    commands_payload: object = None
    state_payload: object = None
    deadline = time.time() + timeout
    try:
        proc.stdin.write(json.dumps({"id": "cmds", "type": "get_available_commands"}) + "\n")
        proc.stdin.write(json.dumps({"id": "state", "type": "get_state"}) + "\n")
        proc.stdin.flush()
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            if frame.get("type") != "response":
                continue
            if frame.get("id") == "cmds":
                commands_payload = frame.get("data")
            elif frame.get("id") == "state":
                state_payload = frame.get("data")
            if commands_payload is not None and state_payload is not None:
                break
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
    if commands_payload is None or state_payload is None:
        raise RuntimeError("omp rpc handshake did not deliver commands/state")
    return {"commands": commands_payload, "state": state_payload}


# --------------------------------------------------------------------------- #
# runtime side: parsing
# --------------------------------------------------------------------------- #
def system_prompt_text(state: object) -> str:
    if not isinstance(state, dict):
        return ""
    prompt = state.get("systemPrompt")
    if isinstance(prompt, list):
        return "\n".join(p for p in prompt if isinstance(p, str))
    if isinstance(prompt, str):
        return prompt
    return ""


def block(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1) if match else ""


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def same_description(want: str, have: str) -> bool:
    """Compare a repo description with the description omp advertises.

    The session prompt truncates long descriptions and marks the cut with an
    ellipsis, so a truncated runtime description is a prefix of ours.
    """
    want = normalize(want)
    have = normalize(have)
    if not want or not have:
        return False
    if want == have:
        return True
    trimmed = have[:-1].rstrip() if have.endswith("…") else have
    if len(trimmed) >= 20 and want.startswith(trimmed):
        return True
    if len(want) >= 20 and have.startswith(want):
        return True
    return False


def parse_skills(prompt: str) -> dict[str, str]:
    body = block(prompt, "skills")
    found: dict[str, str] = {}
    for line in body.splitlines():
        match = re.match(r"^-\s+([A-Za-z0-9._-]+):\s*(.*)$", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


def parse_rules(prompt: str) -> dict[str, str]:
    body = block(prompt, "domain-rules") or block(prompt, "rules")
    found: dict[str, str] = {}
    for line in body.splitlines():
        match = re.match(r"^-\s+([A-Za-z0-9._-]+)\s*(?:\([^)]*\))?:\s*(.*)$", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


def parse_commands(payload: object) -> dict[str, str]:
    items: list = []
    if isinstance(payload, dict):
        for key in ("commands", "items", "entries"):
            if isinstance(payload.get(key), list):
                items = payload[key]
                break
    elif isinstance(payload, list):
        items = payload
    found: dict[str, str] = {}
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("command") or item.get("id")
            if isinstance(name, str):
                found[name] = item.get("description") or ""
        elif isinstance(item, str):
            found[item] = ""
    return found


def parse_agents(state: object) -> dict[str, str]:
    found: dict[str, str] = {}
    if not isinstance(state, dict):
        return found
    for tool in state.get("dumpTools") or []:
        if not isinstance(tool, dict) or tool.get("name") != "task":
            continue
        description = tool.get("description") or ""
        section = re.search(r"#\s*Available Agents\s*\n(.*)", description, re.DOTALL)
        if not section:
            continue
        for line in section.group(1).splitlines():
            match = re.match(r"^-\s+`([^`]+)`\s*(?:\([^)]*\))?\s*[:—]\s*(.*)$", line)
            if match:
                found[match.group(1)] = match.group(2)
    return found


def skill_list(omp_bin: str) -> dict[str, str]:
    """Enumerate the skills omp serves, with the description it resolved.

    `omp skill list` is a second, independent view of the same runtime: it
    prints one line per discovered skill as `name<TAB>description`. The session
    prompt truncates descriptions and can be taken over by a same-named skill
    from another provider, so this view is the one that shows which text omp
    actually serves under a given name.
    """
    proc = subprocess.run(
        [omp_bin, "skill", "list"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"omp skill list failed: {proc.stdout.strip()} {proc.stderr.strip()}"
        )
    found: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        name = parts[0].strip()
        if name:
            found.setdefault(name, parts[1].strip() if len(parts) > 1 else "")
    return found


def collect(omp_bin: str, cwd: str, ours: dict[str, str]) -> dict:
    """Read what the runtime advertises, plus the evidence that it really did.

    `assets` holds the advertised names per kind. `meta` carries the proof
    that the probe was not blind: whether the runtime exposed each surface at
    all (`blocks`), how many entries it listed (`advertised`), and whether a
    user-level control skill outside this fork was seen (`control`).
    """
    raw = rpc_probe(omp_bin, cwd)
    prompt = system_prompt_text(raw["state"])
    skills = parse_skills(prompt)
    rules = parse_rules(prompt)
    commands = parse_commands(raw["commands"])
    agents = parse_agents(raw["state"])
    controls = control_skills(ours)
    listed = skill_list(omp_bin)
    return {
        "assets": {
            "skills": skills,
            "commands": commands,
            "rules": rules,
            "agents": agents,
        },
        "listed": listed,
        "meta": {
            "blocks": {
                "skills": bool(block(prompt, "skills")),
                "commands": bool(commands),
                "rules": bool(block(prompt, "domain-rules") or block(prompt, "rules")),
                "agents": bool(agents),
            },
            "advertised": {
                "skills": len(skills),
                "commands": len(commands),
                "rules": len(rules),
                "agents": len(agents),
            },
            "listed_total": len(listed),
            "control_expected": controls,
            "control": [name for name in controls if name in skills],
        },
    }


# --------------------------------------------------------------------------- #
# plugin state
# --------------------------------------------------------------------------- #
def plugin_enabled(omp_bin: str) -> bool | None:
    proc = subprocess.run(
        [omp_bin, "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    stack: list = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            name = node.get("name") or node.get("id") or node.get("package")
            if name == PLUGIN_NAME and isinstance(node.get("enabled"), bool):
                return node["enabled"]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def set_plugin_enabled(omp_bin: str, enabled: bool) -> None:
    action = "enable" if enabled else "disable"
    proc = subprocess.run(
        [omp_bin, "plugin", action, PLUGIN_NAME],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"omp plugin {action} failed: {proc.stdout.strip()} {proc.stderr.strip()}"
        )


def plugin_root(omp_bin: str) -> Path | None:
    """Return the directory omp links this fork from, or None when it is absent."""
    proc = subprocess.run(
        [omp_bin, "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    for section in ("npm", "marketplace"):
        for entry in data.get(section) or []:
            if entry.get("name") == PLUGIN_NAME and entry.get("path"):
                return Path(entry["path"])
    return None


# --------------------------------------------------------------------------- #
# install side: repo tree vs installed plugin root
# --------------------------------------------------------------------------- #
SKIP_DIRS = {"__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_files(root: Path) -> dict[str, str]:
    """relative path -> sha256 for every file the plugin root ships."""
    files: dict[str, str] = {}
    for kind in KINDS:
        base = root / kind
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if SKIP_DIRS & set(path.parts):
                continue
            files[path.relative_to(root).as_posix()] = sha256_file(path)
    for name in ("package.json", "LICENSE", "NOTICE.md"):
        path = root / name
        if path.is_file():
            files[name] = sha256_file(path)
    return files


def install_drift(repo_root: Path, install_root: Path) -> dict[str, list[str]]:
    """Report how the installed plugin root differs from the repository tree."""
    repo_files = asset_files(repo_root)
    install_files = asset_files(install_root)
    return {
        "missing": sorted(set(repo_files) - set(install_files)),
        "extra": sorted(set(install_files) - set(repo_files)),
        "changed": sorted(
            path
            for path in set(repo_files) & set(install_files)
            if repo_files[path] != install_files[path]
        ),
    }


# --------------------------------------------------------------------------- #
# comparison
# --------------------------------------------------------------------------- #
def compare(
    expected: dict[str, dict[str, str]],
    seen: dict[str, dict[str, str]],
    listed: dict[str, str] | None = None,
) -> dict:
    """Split each kind into served / compressed / conflict / missing.

    Ownership of a name is decided by the text the runtime *resolved* for it,
    not by the line the session prompt prints. omp shortens long skill
    descriptions before they go into the prompt and caches the result in
    `~/.omp/agent/skill-descriptions.db`, so the prompt line of a skill this
    repo ships regularly differs from the frontmatter text without the skill
    belonging to anybody else. For skills the resolved text comes from
    `omp skill list`; for commands, rules and agents the prompt line is the
    only view there is.

    served    the name is advertised with this repo's text
    compressed the name is advertised and resolves to this repo's skill, but
              the prompt shows a shortened description
    conflict  the name is advertised with text that is not this repo's, so
              somebody else owns the name
    missing   the name is not advertised at all
    """
    result: dict[str, dict] = {}
    for kind in KINDS:
        want, have = expected[kind], seen[kind]
        served: list[str] = []
        compressed: list[str] = []
        conflict: list[str] = []
        missing: list[str] = []
        for name, description in want.items():
            if name not in have:
                missing.append(name)
                continue
            advertised = have[name]
            if kind == "skills" and listed is not None:
                if name not in listed or not same_description(description, listed[name]):
                    conflict.append(name)
                    continue
                if same_description(description, advertised):
                    served.append(name)
                else:
                    compressed.append(name)
            elif same_description(description, advertised):
                served.append(name)
            else:
                conflict.append(name)
        item = {
            "expected": len(want),
            "served": sorted(served),
            "compressed": sorted(compressed),
            "conflict": sorted(conflict),
            "missing": sorted(missing),
        }
        if kind == "skills" and listed is not None:
            ours_listed = [
                name
                for name, description in want.items()
                if name in listed and same_description(description, listed[name])
            ]
            foreign = [
                name
                for name, description in want.items()
                if name in listed and not same_description(description, listed[name])
            ]
            absent = [name for name in want if name not in listed]
            item["listed_ours"] = sorted(ours_listed)
            item["listed_foreign"] = sorted(foreign)
            item["listed_absent"] = sorted(absent)
        result[kind] = item
    return result


def print_report(label: str, data: dict, meta: dict) -> None:
    print(f"== {label} ==")
    for kind in KINDS:
        item = data[kind]
        print(
            f"  {kind:<9} expected={item['expected']:<3} served={len(item['served']):<3} "
            f"compressed={len(item['compressed']):<3} conflict={len(item['conflict']):<3} "
            f"missing={len(item['missing']):<3} "
            f"advertised={meta['advertised'][kind]:<4} "
            f"block={'yes' if meta['blocks'][kind] else 'no'}"
        )
        for label_text, key in (
            ("missing", "missing"),
            ("conflict", "conflict"),
            ("compressed", "compressed"),
        ):
            if item[key]:
                print(f"            {label_text}: {', '.join(item[key][:12])}")
        if kind == "skills" and "listed_ours" in item:
            print(
                f"            omp skill list: ours={len(item['listed_ours'])} "
                f"foreign={len(item['listed_foreign'])} absent={len(item['listed_absent'])}"
            )
    print(
        "  control skills: expected="
        + (", ".join(meta["control_expected"]) or "none")
        + " advertised="
        + (", ".join(meta["control"]) or "none")
    )
    compressed = len(data["skills"]["compressed"])
    if compressed:
        print(
            f"  note: {compressed} skills are advertised with a shortened description; "
            "omp caches those in ~/.omp/agent/skill-descriptions.db, `omp skill list` "
            "shows the full text"
        )


def verdict(
    kind_results: dict,
    meta: dict,
    plugin_is_enabled: bool,
    expected_counts: dict,
) -> tuple[list[str], list[str]]:
    """Split observations into failures and warnings.

    The probe has to be trustworthy before "nothing is served" means anything.
    A runtime that advertises fewer entries than this repo ships, or that lost
    the user-level control skills, would look exactly like a clean disable, so
    those cases are failures of their own: the state is *undetermined*, not
    clean.
    """
    failures: list[str] = []
    warnings: list[str] = []
    advertised = meta["advertised"]
    blocks = meta["blocks"]

    if meta["control_expected"] and not meta["control"]:
        failures.append(
            "control skills "
            + ", ".join(meta["control_expected"])
            + " are not advertised - the skills block could not be read, so an "
            "empty result is not evidence that the plugin serves nothing"
        )

    for kind in KINDS:
        if plugin_is_enabled:
            if advertised[kind] < expected_counts[kind]:
                failures.append(
                    f"{kind}: the runtime advertises {advertised[kind]} entries but this "
                    f"repo ships {expected_counts[kind]} - the probe cannot be trusted"
                )
        elif kind != "rules" and advertised[kind] == 0 and not blocks[kind]:
            failures.append(
                f"{kind}: the runtime exposed no {kind} surface at all - visibility "
                "cannot be determined"
            )

    for kind in KINDS:
        item = kind_results[kind]
        if plugin_is_enabled:
            if item["missing"]:
                failures.append(
                    f"{kind}: {len(item['missing'])} assets missing while the plugin is enabled"
                    + (f" -> {', '.join(item['missing'][:12])}" if item["missing"] else "")
                )
            if item["conflict"]:
                failures.append(
                    f"{kind}: {len(item['conflict'])} assets are advertised with another "
                    "provider's text while the plugin is enabled"
                    + (f" -> {', '.join(item['conflict'][:12])}" if item["conflict"] else "")
                )
        else:
            if item["served"]:
                failures.append(
                    f"{kind}: {len(item['served'])} assets still served while the plugin is disabled"
                    + (f" -> {', '.join(item['served'][:12])}" if item["served"] else "")
                )

    skills = kind_results["skills"]
    if plugin_is_enabled:
        if skills.get("listed_absent"):
            failures.append(
                f"skills: {len(skills['listed_absent'])} skills are not served with this "
                "repo's descriptions while the plugin is enabled"
                + (f" -> {', '.join(skills['listed_absent'][:12])}" if skills["listed_absent"] else "")
            )
        if skills.get("listed_foreign"):
            failures.append(
                f"skills: {len(skills['listed_foreign'])} skills are listed under another "
                "provider's description while the plugin is enabled"
                + (f" -> {', '.join(skills['listed_foreign'][:12])}" if skills["listed_foreign"] else "")
            )
    elif skills.get("listed_ours"):
        failures.append(
            f"skills: {len(skills['listed_ours'])} skills are still served with this "
            "repo's descriptions while the plugin is disabled"
            + (f" -> {', '.join(skills['listed_ours'][:12])}" if skills["listed_ours"] else "")
        )
    return failures, warnings


def find_omp() -> str:
    """Locate the omp executable.

    The binary is on PATH for a normal install, and the Windows launcher
    keeps it under the Tern install directory, so both are tried. OMP_BIN
    overrides both, which is what a different install needs.
    """
    override = os.environ.get("OMP_BIN")
    if override:
        return override
    found = shutil.which("omp")
    if found:
        return found
    tern = Path.home() / "AppData" / "Local" / "Tern" / "omp" / "bin" / "omp.exe"
    if tern.exists():
        return str(tern)
    return "omp"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--probe", action="store_true", help="read-only visibility report")
    mode.add_argument(
        "--toggle-test",
        action="store_true",
        help="disable plugin, probe, re-enable, probe; always restores prior state",
    )
    parser.add_argument(
        "--omp",
        default=None,
        help="path to the omp executable (default: OMP_BIN, then PATH, then the Windows launcher)",
    )
    parser.add_argument("--cwd", default=str(REPO_ROOT), help="working directory for the omp process")
    parser.add_argument(
        "--root",
        default=None,
        help="tree that defines this fork's assets (default: the installed plugin root, else the repo tree)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    omp_bin = args.omp or find_omp()
    if shutil.which(omp_bin) is None and not Path(omp_bin).exists():
        print(f"error: omp executable not found: {omp_bin}", file=sys.stderr)
        return 2

    expected_root = Path(args.root) if args.root else (plugin_root(omp_bin) or REPO_ROOT)
    expected = repo_inventory(expected_root)
    payload: dict = {
        "expected_counts": {kind: len(expected[kind]) for kind in KINDS},
        "expected_root": str(expected_root),
    }
    failures: list[str] = []
    warnings: list[str] = []

    install_root = plugin_root(omp_bin)
    if install_root is not None:
        drift = install_drift(REPO_ROOT, install_root)
        payload["install_drift"] = drift
        if drift["missing"] or drift["extra"] or drift["changed"]:
            failures.append(
                "the installed plugin root differs from the repo tree "
                f"({len(drift['missing'])} missing, {len(drift['extra'])} extra, "
                f"{len(drift['changed'])} changed) - run python tools/deploy.py"
            )

    if args.toggle_test:
        before = plugin_enabled(omp_bin)
        payload["enabled_before"] = before
        try:
            set_plugin_enabled(omp_bin, False)
            disabled_collect = collect(omp_bin, args.cwd, expected["skills"])
            payload["disabled"] = compare(
                expected, disabled_collect["assets"], disabled_collect["listed"]
            )
            payload["disabled_meta"] = disabled_collect["meta"]
            set_plugin_enabled(omp_bin, True)
            enabled_collect = collect(omp_bin, args.cwd, expected["skills"])
            payload["enabled"] = compare(
                expected, enabled_collect["assets"], enabled_collect["listed"]
            )
            payload["enabled_meta"] = enabled_collect["meta"]
        finally:
            set_plugin_enabled(omp_bin, bool(before) if before is not None else True)
        payload["enabled_after"] = plugin_enabled(omp_bin)
        disabled_failures, _ = verdict(
            payload["disabled"], payload["disabled_meta"], False, payload["expected_counts"]
        )
        enabled_failures, enabled_warnings = verdict(
            payload["enabled"], payload["enabled_meta"], True, payload["expected_counts"]
        )
        failures += disabled_failures + enabled_failures
        warnings += enabled_warnings
    else:
        state = plugin_enabled(omp_bin)
        payload["enabled"] = state
        observed = collect(omp_bin, args.cwd, expected["skills"])
        payload["observed"] = compare(expected, observed["assets"], observed["listed"])
        payload["observed_meta"] = observed["meta"]
        observed_failures, observed_warnings = verdict(
            payload["observed"], observed["meta"], state is not False, payload["expected_counts"]
        )
        failures += observed_failures
        warnings += observed_warnings

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key in ("disabled", "enabled", "observed"):
            value = payload.get(key)
            meta = payload.get(f"{key}_meta")
            if (
                isinstance(value, dict)
                and isinstance(meta, dict)
                and all(kind in value for kind in KINDS)
            ):
                print_report(key, value, meta)

    stream = sys.stderr if args.json else sys.stdout
    for line in warnings:
        print(f"WARN {line}", file=stream)
    if failures:
        print("\nFAIL", file=stream)
        for line in failures:
            print(f"  - {line}", file=stream)
        return 1
    print("\nPASS", file=stream)
    return 0


if __name__ == "__main__":
    sys.exit(main())
