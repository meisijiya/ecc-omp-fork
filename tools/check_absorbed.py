#!/usr/bin/env python
"""Gate: the absorbed pool must still be the pool the manifest describes.

    python tools/check_absorbed.py            # human readable
    python tools/check_absorbed.py --json     # machine readable

The absorbed pool is third-party skill text this fork rewrote and ships as
its own (ADR-0010).  Nothing regenerates it except tools/sync_absorbed.py, so
five things can drift, and each is a defect:

  1. manifest/absorbed.json is malformed -- a source without a 40 character
     commit, or a skill entry without a source or path.
  2. a stored file was edited by hand, deleted, or added: the digest set no
     longer matches the manifest.
  3. the generated bundle skill no longer equals what its stored inputs
     produce -- someone edited the generated file instead of the rules.
  4. an absorbed source lost its license text, or the text no longer carries
     the copyright line the manifest declares (MIT requires both to travel
     with the content).
  5. a stored skill still carries text the adaptation invariants forbid
     (`CLAUDE.md`, `.claude/`, `disable-model-invocation`, a slash trigger
     the rules were supposed to strip).

Offline, repeatable, no network: the same tree always produces the same
report.  Exit 0 clean, 1 defects, 2 unreadable input.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import absorbed_fixups  # noqa: E402
import sync_absorbed  # noqa: E402

ROOT = sync_absorbed.ROOT
ABSORBED = sync_absorbed.ABSORBED
MANIFEST = sync_absorbed.MANIFEST

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Text the stored copy must never carry: INV-02/03/15 and the two
# host-specific frontmatter keys the rules drop.
SLASH_TRIGGERS = (
    "correct", "sharpen", "statechart", "typescript-best-practices",
    "constraint-driven-development", "engineering-principles",
)

FORBIDDEN = [
    (re.compile(r"`?CLAUDE\.md`?", re.I), "CLAUDE.md reference (INV-02)"),
    (re.compile(r"\.claude/"), ".claude/ path (INV-03)"),
    (re.compile(r"\.codex/"), "foreign harness path"),
    (re.compile(r"\bClaude Code\b"), "Claude Code wording (INV-15)"),
    (re.compile(r"`?claude\s+-p\b"), "Claude CLI invocation (INV-04)"),
    (re.compile(r"`AskUserQuestion`|\bTodoWrite\b"), "Claude tool name (INV-05)"),
    # only the frontmatter form counts: a fenced YAML example may show `paths:`
    (re.compile(r"^disable-model-invocation:", re.M), "host-specific frontmatter key"),
    (re.compile(r"^paths: \[", re.M), "host-specific frontmatter key"),
    (re.compile(r"(?<![\w`])/(?:%s)\b" % "|".join(SLASH_TRIGGERS)),
     "slash trigger (INV-14)"),
]


def defect(findings, kind, where, detail):
    findings.append({"kind": kind, "file": where, "detail": detail})


def check_manifest(findings):
    try:
        manifest = json.load(open(MANIFEST, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read {MANIFEST}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(manifest, dict):
        print(f"{MANIFEST} is not a JSON object", file=sys.stderr)
        raise SystemExit(2)
    sources = manifest.get("sources") or {}
    if not sources:
        defect(findings, "manifest", "manifest/absorbed.json", "no sources declared")
    for slug, spec in sources.items():
        if not isinstance(spec.get("repo"), str) or "://" not in spec["repo"]:
            defect(findings, "manifest", f"sources/{slug}", "repo is not a URL")
        if not SHA_RE.match(str(spec.get("commit", ""))):
            defect(findings, "manifest", f"sources/{slug}", "commit is not a 40 character sha")
        license_spec = spec.get("license") or {}
        license_path = os.path.join(ABSORBED, slug, license_spec.get("file", "LICENSE"))
        if not os.path.isfile(license_path):
            defect(findings, "license", license_path,
                   "MIT requires the upstream license text to travel with the content")
        else:
            text = open(license_path, encoding="utf-8", errors="replace").read()
            if license_spec.get("copyright") not in text:
                defect(findings, "license", license_path,
                       "does not carry the declared copyright line")
            if "MIT License" not in text:
                defect(findings, "license", license_path, "not an MIT license text")
    skills = manifest.get("skills") or {}
    if not skills:
        defect(findings, "manifest", "manifest/absorbed.json", "no skills declared")
    for name, entry in skills.items():
        if entry.get("source") not in sources:
            defect(findings, "manifest", f"skills/{name}", "unknown source")
        if not entry.get("path"):
            defect(findings, "manifest", f"skills/{name}", "no path")
        if not entry.get("files"):
            defect(findings, "manifest", f"skills/{name}", "no file digests")
    bundle = manifest.get("bundle") or {}
    if bundle.get("source") not in sources:
        defect(findings, "manifest", "bundle", "unknown source")
    if bundle.get("skill") not in skills:
        defect(findings, "manifest", "bundle", "bundle skill is not declared in skills")
    if not bundle.get("from"):
        defect(findings, "manifest", "bundle", "no inputs")
    for name, entry in skills.items():
        path = str(entry.get("path") or "").rstrip("/")
        leaf = path.split("/")[-1]
        if leaf and leaf != name:
            defect(findings, "manifest", f"skills/{name}",
                   f"path ends in {leaf!r}; apply_selection names the directory"
                   f" after the manifest key")
    return manifest


def check_digests(manifest, findings):
    for name, entry in (manifest.get("skills") or {}).items():
        source, path = entry.get("source"), entry.get("path")
        if not source or not path:
            continue  # already reported by check_manifest
        base = os.path.join(ABSORBED, source, path)
        actual = sync_absorbed.digest_tree(base) if os.path.isdir(base) else {}
        expected = entry.get("files") or {}
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        for rel in missing:
            defect(findings, "digest", f"{base}/{rel}", "declared in manifest, absent on disk")
        for rel in extra:
            defect(findings, "digest", f"{base}/{rel}", "present on disk, absent from manifest")
        for rel in sorted(set(expected) & set(actual)):
            if expected[rel] != actual[rel]:
                defect(findings, "digest", f"{base}/{rel}", "content differs from the manifest digest")
    bundle = manifest.get("bundle") or {}
    if not bundle.get("source"):
        return
    base = os.path.join(ABSORBED, bundle["source"], "principles")
    actual = sync_absorbed.digest_tree(base) if os.path.isdir(base) else {}
    for rel in sorted(set(bundle["files"]) - set(actual)):
        defect(findings, "digest", f"{base}/{rel}", "bundle input missing")
    for rel in sorted(set(actual) - set(bundle["files"])):
        defect(findings, "digest", f"{base}/{rel}",
               "bundle input present on disk, absent from manifest")
    for rel in sorted(set(bundle["files"]) & set(actual)):
        if bundle["files"][rel] != actual[rel]:
            defect(findings, "digest", f"{base}/{rel}", "bundle input differs from the manifest digest")


def check_bundle(manifest, findings):
    bundle = manifest.get("bundle") or {}
    if not bundle.get("source") or not bundle.get("path"):
        return
    target = os.path.join(ABSORBED, bundle["source"], bundle["path"], "SKILL.md")
    if not os.path.isfile(target):
        defect(findings, "bundle", target, "generated bundle skill is missing")
        return
    stored = open(target, encoding="utf-8").read()
    try:
        regenerated = sync_absorbed.bundle_text(bundle)
    except SystemExit as exc:
        defect(findings, "bundle", target, str(exc))
        return
    if stored != regenerated:
        defect(findings, "bundle", target,
               "generated file does not match its inputs; rerun tools/sync_absorbed.py")


def check_line_endings(findings):
    """A CRLF checkout changes every digest the manifest records."""
    for dirpath, _dirnames, filenames in os.walk(ABSORBED):
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            with open(p, "rb") as f:
                if b"\r\n" in f.read():
                    defect(findings, "line-endings", p,
                           "CRLF in the absorbed pool; .gitattributes forces LF,"
                           " so a clean clone would digest differently")


def check_forbidden(manifest, findings):
    for name, entry in (manifest.get("skills") or {}).items():
        if not entry.get("source") or not entry.get("path"):
            continue
        base = os.path.join(ABSORBED, entry["source"], entry["path"])
        if not os.path.isdir(base):
            continue
        for rel in sync_absorbed.digest_tree(base):
            if not rel.endswith(".md"):
                continue
            text = open(os.path.join(base, rel), encoding="utf-8").read()
            for pattern, why in FORBIDDEN:
                if pattern.search(text):
                    defect(findings, "invariant",
                           entry["source"] + "/" + entry["path"] + "/" + rel, why)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    findings = []
    manifest = check_manifest(findings)
    check_digests(manifest, findings)
    check_bundle(manifest, findings)
    check_line_endings(findings)
    check_forbidden(manifest, findings)

    if args.json:
        print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("absorbed pool: consistent (%d skills)" % len(manifest["skills"]))
        for f in findings:
            print(f"{f['kind']}: {f['file']}: {f['detail']}")
        print("\n%d defect(s)" % len(findings))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
