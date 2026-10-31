#!/usr/bin/env python
"""Deploy the materialized fork assets into the omp plugin install directory.

The fork repository is the source of truth. This script copies only the
runtime surface (skills/ commands/ agents/ rules/ + package.json + LICENSE +
NOTICE.md) into the directory omp links as a plugin, so the plugin tree stays
free of pool/, tools/ and the git metadata.

Guards (each one exists because the failure it prevents is silent):

  * the materialized tree must match the recorded selection -- if
    manifest/selection.json changed but tools/apply_selection.py was not
    re-run, the deploy would ship the previous profile's assets;
  * every runtime source directory must exist -- a missing one used to be
    reported as a string and deployed anyway;
  * the copy is atomic (temp dir + rename) so omp never observes a half
    written plugin tree;
  * after linking, the skill names omp actually enumerates are compared with
    the materialized skill names -- `omp plugin list` only proves the plugin
    was claimed, not that its skills are reachable;
  * legacy plugins from earlier layouts are removed, because a stale
    JUNCTION in omp's plugin tree silently injects a second copy of every
    skill into the system prompt.

    python tools/deploy.py             # sync, link, verify
    python tools/deploy.py --uninstall # remove the linked plugin
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(os.path.expanduser("~"), ".omp", "agent", "local", "ecc-omp-fork")
RUNTIME = ("skills", "agents", "rules")
# This fork ships no commands; an older deploy may have left them in the
# install root, where omp would keep advertising them.
STALE_DIRS = ("commands",)
EXTRA_FILES = ("package.json", "LICENSE", "NOTICE.md")
LEGACY_PLUGINS = ("ecc-pi-core", "ecc-programming")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_materialized_matches_selection():
    """Refuse to deploy a tree that does not match the recorded selection.

    tools/apply_selection.py writes manifest/applied.json when it materializes.
    If the user edits manifest/selection.json and deploys without
    re-materializing, the tree on disk is the previous profile's -- a silent
    wrong-profile deploy.
    """
    selection_path = os.path.join(ROOT, "manifest", "selection.json")
    applied_path = os.path.join(ROOT, "manifest", "applied.json")
    if not os.path.isfile(applied_path):
        raise SystemExit(
            "manifest/applied.json is missing -- run `python tools/apply_selection.py` "
            "before deploying"
        )
    selection = read_json(selection_path)
    applied = read_json(applied_path)
    if applied.get("profile") != selection.get("active_profile"):
        raise SystemExit(
            f"materialized tree is profile {applied.get('profile')!r} but "
            f"manifest/selection.json selects {selection.get('active_profile')!r} -- "
            f"run `python tools/apply_selection.py` then deploy again"
        )


def sync_dir(name):
    """Copy one runtime directory into the install dir, atomically."""
    src = os.path.join(ROOT, name)
    dst = os.path.join(INSTALL, name)
    if not os.path.isdir(src):
        raise SystemExit(f"{name}: source directory missing at {src}")
    tmp = dst + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.rename(tmp, dst)
    n = len(os.listdir(dst))
    return f"{name}: {n} entries -> {dst}"


def remove_legacy():
    """Remove plugins left over from earlier layouts of this fork.

    A stale JUNCTION under omp's plugin tree keeps its skills discoverable, so
    the same skills are injected into the system prompt twice.
    """
    for name in LEGACY_PLUGINS:
        r = subprocess.run(
            ["omp", "plugin", "uninstall", name], capture_output=True, text=True
        )
        out = (r.stdout + r.stderr).strip()
        if out:
            print(f"legacy {name}: {out}")
        legacy_dir = os.path.join(os.path.expanduser("~"), ".omp", "agent", "local", name)
        if os.path.isdir(legacy_dir):
            shutil.rmtree(legacy_dir)
            print(f"legacy {name}: removed {legacy_dir}")


def verify_skills():
    """Compare the materialized skill names with the ones omp enumerates."""
    expected = {
        n
        for n in os.listdir(os.path.join(ROOT, "skills"))
        if os.path.isdir(os.path.join(ROOT, "skills", n))
    }
    r = subprocess.run(["omp", "skill", "list"], capture_output=True, text=True)
    if r.returncode != 0:
        print("verify: `omp skill list` failed:", (r.stdout + r.stderr).strip())
        return False
    found = set()
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        found.add(line.split("\t")[0].strip())
    missing = sorted(expected - found)
    if missing:
        print(f"verify: {len(missing)} materialized skills not enumerated by omp:")
        for n in missing:
            print(f"  - {n}")
        print("verify: restart omp (or /reload-plugins) so it re-scans the plugin tree")
        return False
    print(f"verify: all {len(expected)} materialized skills are enumerated by omp")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument(
        "--skip-verify",
        action="store_true",
        help="skip the `omp skill list` enumeration check",
    )
    args = ap.parse_args()

    if args.uninstall:
        subprocess.run(["omp", "plugin", "uninstall", "ecc-omp-fork"], check=False)
        if os.path.isdir(INSTALL):
            shutil.rmtree(INSTALL)
        print("removed", INSTALL)
        return

    check_materialized_matches_selection()

    os.makedirs(INSTALL, exist_ok=True)
    for name in RUNTIME:
        print(sync_dir(name))
    for name in STALE_DIRS:
        dst = os.path.join(INSTALL, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
            print(f"{name}: removed stale {dst}")
    for name in EXTRA_FILES:
        src = os.path.join(ROOT, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(INSTALL, name))
            print(f"{name} -> {INSTALL}")
        else:
            print(f"{name}: not found in repo root, skipped")

    remove_legacy()

    # Link the deployed directory into omp's plugin tree. Re-linking an
    # already linked directory is a no-op, not an error.
    r = subprocess.run(["omp", "plugin", "link", INSTALL], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print(out)
    if r.returncode != 0:
        print(f"link failed with exit code {r.returncode}")

    r = subprocess.run(["omp", "plugin", "list"], capture_output=True, text=True)
    print(r.stdout.strip())

    if not args.skip_verify and not verify_skills():
        sys.exit(1)
    print("\nnote: skills are picked up on reload; new agents need a new session")


if __name__ == "__main__":
    main()
