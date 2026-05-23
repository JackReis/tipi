# Tipi — Rbitr (Arbiter) Integration

This document outlines how the **Tipi** portable core integrates into the **rbitr** (Arbiter) Symphony orchestration topology.

For the canonical high-level topology and roster, refer to:
- [AGENT_DESIGN.md](file:///Users/jack.reis/Documents/=notes/AGENT_DESIGN.md) (Main Vault)
- [rbitr-design.md](file:///Users/jack.reis/Documents/=notes/docs/architecture/rbitr-design.md) (Main Vault)

## 1. Architectural Role

In the **rbitr** topology, **Tipi** acts as the **portable core and dispatch interface** (the IDE-agnostic enclosure seam).

It is responsible for:
- **Authoritative Intent Mapping:** Maintains the `tipi/contract/runtime-dispatch.yaml` configuration which defines the mappings from intent to execution.
- **Dispatch Action:** Exposes the `dispatch_rbitr` (and legacy `dispatch_arbiter`) intents. Callers load these intents to issue execution requests (Bare or Sinew envelopes) directly to the local `rbitr` server API on port `8765`.
- **Identity Resolution:** Documents and references the roles of sub-agents (Hermes, Codex, Zoe) under the adjudicant orchestrator pattern.

## 2. Intent Specification (`runtime-dispatch.yaml`)

Tipi implements the following specific orchestrator intents:

- **`dispatch_rbitr`:** Post execution request to the evolved Rbitr server on `:8765`. It uses a stdlib Python subprocess execution structure, keeping Tipi free of heavy external HTTP client package requirements.
- **`dispatch_arbiter`:** Maintained for backwards compatibility; maps to the same HTTP endpoint and payloads.

All dispatch payloads require `ARBITER_ADMIN_TOKEN` present in the environment (sourced from SOPS at launch).

## 3. Dataflow Integration

```
   Intent (e.g. dispatch_rbitr)
         │
         ▼
   Tipi Runtime Subprocess
         │
         ▼
   urllib POST Request
         │
         ├─── Token: Bearer $ARBITER_ADMIN_TOKEN
         ├─── Header: Content-Type: application/json
         ├─── Target: http://127.0.0.1:8765/dispatch
         │
         ▼
   rbitr Server Endpoint
```
