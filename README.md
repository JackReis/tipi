# tipi

Portable fleet core for the agentic AI fleet. IDE-agnostic. Consumed by enclosures (`vs-tipi`, future `cursor-tipi`, etc.).

## What this is

A tipi is a minimal movable shelter — the fleet's gathering place to express, refresh, and refine context. This repo contains the poles and the cover; enclosures pick the location.

## Layers consumed

Per the three-layer consciousness ADR (lives in the vault at `docs/architecture/three-layer-consciousness.md`):

- **Body** — `neural-garden` (the `=notes` vault) + sibling repos + OS
- **Mind** — OBn (ChromaDB) or Khoj (if it returns), knowledge-graph MCP, MEMORY.md, project_memory.json
- **Spirit** — OB1 v2 belief-ledger (future)
- **Epigenetics** (modulating input, not a layer) — Nate's PromptKit

`tipi` is a **view**, never a **source**. All writes go through the runtime CLIs or the consciousness interface.

## Layout

```
tipi/
  mcp/
    consciousness/   # body/mind/spirit readers — stable interface seam
    dizzy/           # Discord dispatch wrapper (Wings / Zoe / Codex lanes)
    hermes/          # Hermes runtime dispatch wrapper
    openclaw/        # OpenClaw (OLIVIER_MBP / KimiClaw) runtime dispatch wrapper
    claude_spawn/    # Fresh Claude Code session dispatch
    epigenetics/     # Nate's PromptKit wrapper
  contract/          # schemas, agent contract, runtime-dispatch.yaml
  tests/
```

## Shared contract with the infra-context-dashboard

`tipi/contract/consciousness-interface.py` (Python Protocol) is the source of truth. The schema published as JSON Schema (future Task 9.2 in the plan) is generated from it.

## Fleet Integration & Rbitr

This portable core provides the authoritative `runtime-dispatch.yaml` mapping used by the fleet to issue dispatch intents (`dispatch_rbitr`) directly to the local `rbitr` Symphony orchestrator on port `8765`.

For detailed architecture, layout, and dataflow integration details, see:
- [docs/RBITR-INTEGRATION.md](docs/RBITR-INTEGRATION.md)

## Status

Scaffolding underway. See `docs/plans/2026-04-21-tipi-vs-tipi.md` in the vault.
