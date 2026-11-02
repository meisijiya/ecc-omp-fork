# AGENTS.md

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `meisijiya/ecc-omp-fork` (via the `gh` CLI; the repo is resolved from the `origin` remote). See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles use identically-named labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Gates

Six gates guard this repo. Run them before declaring work done; each one fails loudly instead of
silently letting a broken asset reach the runtime. Details in `README.md` → 「门禁清单」.

| Command | Guards |
| --- | --- |
| `python tools/check_refs.py` | Dangling references: assets this fork does not provide |
| `python tools/check_adapt.py` | omp adaptation invariants (INV-01..INV-15) |
| `python tools/check_upstream_pin.py` | Upstream pin, its mirror and the pool digest agree |
| `python tools/check_absorbed.py` | Absorbed pool digests, generated bundle and adaptation residue agree |
|`python tools/check_zh_descriptions.py`|Chinese trigger descriptions cover every skill and obey the wording rules|
|`python tools/upstream_versions.py check --offline`|Per-asset version ledger covers every upstream asset|
|`python tools/check_plugin_isolation.py --toggle-test`|Plugin enable/disable visibility (local only; it toggles the plugin)|
