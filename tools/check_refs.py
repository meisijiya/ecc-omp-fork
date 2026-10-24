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

One class of reference is expected rather than a defect. The fork's own
catalog files (own/skills/, own/rules/ and their copies in the runtime tree)
describe the fork as a whole, so they name assets that a narrow profile
crops. The scanner labels those references "not enabled in the active
profile"; the gate reports them and keeps the tree green, because they are
the profile's own description of what else exists.

Usage
  python tools/check_refs.py            # human readable report, exit 1 on defects
  python tools/check_refs.py --json     # machine readable report on stdout

Exit codes
  0  no dangling reference outside the fork's own catalog
  1  dangling references found
  2  the tree could not be inspected (missing manifest / unreadable file)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import refscan  # noqa: E402

CROPPED = "not enabled in the active profile"


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


def classify(findings, fork_owned):
    """Split the findings into defects and profile notices.

    A reference to an asset the active profile cropped is a defect unless it
    sits in one of the fork's own catalog files: upstream content is copied
    with those references removed, so one that survives there is a real
    break. The fork's own files are copied verbatim, so they keep naming the
    assets of the other profiles on purpose.
    """
    defects, notices = [], []
    for f in findings:
        cropped = CROPPED in f.get("reason", "")
        if cropped and f["file"] in fork_owned:
            notices.append(f)
        else:
            defects.append(f)
    return defects, notices


def main(argv):
    try:
        profile = refscan.active_profile()
    except SystemExit as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings = collect()
    defects, notices = classify(findings, refscan.fork_owned_paths())

    if "--json" in argv:
        print(json.dumps({
            "profile": profile,
            "count": len(defects),
            "dangling": defects,
            "profile_cropped_in_fork_catalog": notices,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"profile: {profile}")
        print(f"dangling references: {len(defects)}")
        for f in defects:
            print(f"{f['file']}:{f['line']}: dangling {f['type']} "
                  f"`{f['name']}` -- {f['reason']}")
        if notices:
            print(f"profile-cropped references in the fork's own catalog: "
                  f"{len(notices)}")
            for f in notices:
                print(f"  {f['file']}:{f['line']}: {f['type']} "
                      f"`{f['name']}` -- {f['reason']}")
    return 1 if defects else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
