#!/usr/bin/env python
"""Gate: no asset reference may point at something this fork does not ship.

The model reads a skill and follows what it says. If a line points at a
skill / agent / command that the active profile does not contain, the model
either calls a resource that is not there or invents one. So every such
reference is a defect in the fork, not a cosmetic issue.

The detection lives in tools/refscan.py, which the materializer
(tools/apply_selection.py) also uses to remove the references while upstream
content is copied into the runtime tree. Both sides therefore agree on what
"dangling" means -- a second implementation would either keep the gate red
after a repair or wave through text the model still cannot follow.

Usage
  python tools/check_refs.py            # human readable report, exit 1 on findings
  python tools/check_refs.py --json     # machine readable report on stdout

Exit codes
  0  no dangling reference
  1  dangling references found
  2  the tree could not be inspected (missing manifest / unreadable file)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refscan  # noqa: E402


def collect():
    mat = refscan.materialized_sets()
    pool = refscan.pool_sets()
    kinds = refscan.pool_kind_of(pool)
    findings = []
    for path in refscan.scan_files():
        findings.extend(refscan.check_file(path, mat, pool, kinds))
    # a reference is reported once per (file, line, name, type)
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["name"], f["type"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    unique.sort(key=lambda f: (f["file"], f["line"], f["type"], f["name"]))
    return unique


def main(argv):
    try:
        profile = refscan.active_profile()
    except SystemExit as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings = collect()

    if "--json" in argv:
        print(json.dumps({
            "profile": profile,
            "count": len(findings),
            "dangling": findings,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"profile: {profile}")
        print(f"dangling references: {len(findings)}")
        for f in findings:
            print(f"{f['file']}:{f['line']}: dangling {f['type']} "
                  f"`{f['name']}` -- {f['reason']}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
