#!/usr/bin/env python
"""Gate: the recorded upstream pin must still describe the pool it pins.

    python tools/check_upstream_pin.py

The pin is written by tools/sync_upstream.py right after it refreshes pool/:
manifest/upstream.json holds the upstream commit plus a digest of the pool
content, and manifest/groups.json keeps a hand written copy of the same
commit.  Four things can drift, and each of them is a defect:

  1. manifest/upstream.json is malformed -- the commit is not a 40 character
     hex id, or the repo is missing.  Everything downstream (the CI pin, the
     `git checkout` of the upstream clone) trusts that value.
  2. manifest/groups.json carries a different commit than the pin file.  The
     two are written by different code paths, so the copy can rot unnoticed.
  3. pool/ was changed by hand (or by a partial sync) without the pin being
     updated.  Then the pin describes a pool that is no longer in the
     repository.
  4. NOTICE.md quotes an upstream commit that is not the pinned one.  The
     notice is shipped with the plugin and read by humans, so a stale sha
     there claims a provenance the repository does not have.

The pool digest is recomputed with compute_pool_digest() imported from
tools/sync_upstream.py -- the writer and the checker share one implementation
on purpose: a second copy of the algorithm could disagree on path ordering or
separator bytes and then report a healthy pool as broken.

The tool is local, offline and repeatable: no network, no environment
variables, no clock, no randomness.  The same tree always produces the same
output and the same exit code.

Exit codes
  0  the pin is consistent (all four checks pass)
  1  at least one check failed; every failure is printed
  2  the pin files could not be read (missing file, invalid JSON, unreadable
     pool tree)
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sync_upstream import (  # noqa: E402
    GROUPS_MANIFEST,
    POOL,
    ROOT,
    UPSTREAM_MANIFEST,
    compute_pool_digest,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NOTICE_SHA_RE = re.compile(r"[0-9a-f]{40}", re.IGNORECASE)
NOTICE = os.path.join(ROOT, "NOTICE.md")


class Unreadable(Exception):
    """The pin files (or the pool tree) cannot be inspected."""


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Unreadable(f"{path} does not exist")
    except OSError as exc:
        raise Unreadable(f"{path} cannot be read: {exc}")
    except ValueError as exc:
        raise Unreadable(f"{path} is not valid JSON: {exc}")


def check_manifest_shape(pin):
    """Check 1: the pin file carries a usable commit id and a repo."""
    failures = []
    commit = pin.get("commit")
    if not isinstance(commit, str) or not SHA_RE.match(commit):
        failures.append(
            "manifest/upstream.json: 'commit' is not a 40 character lowercase hex "
            f"commit id: {commit!r}"
        )
    repo = pin.get("repo")
    if not isinstance(repo, str) or not repo.strip():
        failures.append(
            f"manifest/upstream.json: 'repo' is missing or empty: {repo!r}"
        )
    return failures


def check_groups_mirror(pin, groups):
    """Check 2: the hand written copy in groups.json matches the pin file."""
    block = groups.get("upstream")
    if not isinstance(block, dict):
        return ["manifest/groups.json: no top level 'upstream' block"]
    mirrored = block.get("commit")
    pinned = pin.get("commit")
    if mirrored == pinned:
        return []
    return [
        f"manifest/groups.json: upstream.commit {mirrored!r} != "
        f"manifest/upstream.json commit {pinned!r}"
    ]


def check_pool_digest(pin):
    """Check 3: the pool content still hashes to the recorded digest."""
    recorded = pin.get("pool_digest")
    if not isinstance(recorded, str) or not recorded.strip():
        return [
            "manifest/upstream.json: 'pool_digest' is missing; run "
            "python tools/sync_upstream.py to record it"
        ]
    if not os.path.isdir(POOL):
        raise Unreadable(f"{POOL} is not a directory; the pool tree is missing")
    actual = compute_pool_digest(POOL)
    if actual == recorded:
        return []
    return [
        f"pool/: content digest {actual} != manifest/upstream.json pool_digest "
        f"{recorded}; the pool was changed without updating the pin"
    ]


def check_notice_cites_pin(pin):
    """Check 4: NOTICE.md cites exactly the pinned upstream commit."""
    try:
        with open(NOTICE, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        return [f"NOTICE.md cannot be read: {exc}"]
    shas = NOTICE_SHA_RE.findall(text)
    if not shas:
        return ["NOTICE.md does not cite the upstream commit"]
    if len(shas) > 1:
        return [
            f"NOTICE.md cites {len(shas)} upstream commit shas; expected exactly one"
        ]
    cited = shas[0].lower()
    pinned = pin.get("commit")
    pinned = pinned.lower() if isinstance(pinned, str) else pinned
    if cited != pinned:
        return [
            f"NOTICE.md cites upstream commit {cited}, but the pin is {pinned}"
        ]
    return []


def main():
    try:
        pin = load_json(UPSTREAM_MANIFEST)
        groups = load_json(GROUPS_MANIFEST)
    except Unreadable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = [
        # (label, failure prefix, failures): the prefix is what the legacy
        # checks put in front of their detail lines.  The NOTICE.md check
        # states whole sentences, so its prefix stays empty.
        ("manifest/upstream.json shape", "manifest/upstream.json shape: ",
         check_manifest_shape(pin)),
        ("manifest/groups.json mirror", "manifest/groups.json mirror: ",
         check_groups_mirror(pin, groups)),
        ("pool/ digest", "pool/ digest: ", check_pool_digest(pin)),
        ("NOTICE.md cites the pinned upstream commit", "",
         check_notice_cites_pin(pin)),
    ]

    print("upstream pin check")
    print(f"repo:        {pin.get('repo')!r}")
    print(f"commit:      {pin.get('commit')!r}")
    print(f"version:     {pin.get('version')!r}")
    print(f"pool_digest: {pin.get('pool_digest')!r}")

    failed = 0
    for label, prefix, failures in results:
        if failures:
            failed += 1
            for failure in failures:
                print(f"[FAIL] {prefix}{failure}")
        else:
            print(f"[ok] {label}")

    if failed:
        print(f"result: inconsistent ({failed} of {len(results)} checks failed)")
        return 1
    print(f"result: consistent ({len(results)} checks passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
