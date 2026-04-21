# tipi — Repo Guidelines

## Prime directive

`tipi` is a **view**, never a **source**. Never introduce a new write path. All writes to body/mind/spirit go through the runtime CLIs (`hermes`, `openclaw`, `claude`, `dizzy.py`) or through the consciousness layer owners (OBn, Khoj, future OB1 belief-ledger).

## Source of truth for three-layer consciousness

The ADR lives in the vault at `~/Documents/=notes/docs/architecture/three-layer-consciousness.md`. Do not duplicate its content here. Cite it.

## Python setup

- Python 3.11+ required
- `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`
- Tests: `.venv/bin/pytest tests/ -v`

## Commit hygiene

- Explicit-path `git add` (never `git add -A` or `git add .`)
- Conventional-ish commits: `feat(mcp/consciousness): ...`, `test(mcp/dizzy): ...`
- Never force-push to main without explicit user consent

## Coordination

- Coordination with parallel work (infra-context-dashboard) is in `~/Documents/Coordination/2026-04-21-infra-context-dashboard-coordination.md` — un-gitted scratchpad per vault conventions §15.
- Vault plan that governs this repo: `~/Documents/=notes/docs/plans/2026-04-21-tipi-vs-tipi.md`
