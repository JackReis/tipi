# Agent Contract

The one-page contract every agent uses against the three consciousness layers + the epigenetic input, via tipi.

## Prime directive

Tipi is a **view**. Every agent that uses it reads layers through abstract interfaces and writes *only* through the runtime CLIs in `runtime-dispatch.yaml`.

## Reads

| Layer | Via | When |
|---|---|---|
| Body | `BodyReader` Protocol (mcp/consciousness) | Startup (which repos exist, what changed), before dispatch (is anyone committing?) |
| Mind | `MindIndex` Protocol (mcp/consciousness) | Before any non-trivial task (what do I already know?) |
| Spirit | `BeliefLedger` Protocol (mcp/consciousness) | Before decisions that commit to a direction (what do I already believe?) |
| Epigenetics | `tipi-epigenetics` MCP tools | When current arc matches a known kit/guide/post |

## Writes

Agents never write to body/mind/spirit from inside tipi. Writes happen via the proper channel:

| Destination | Channel |
|---|---|
| Body (vault files) | Agent's own file-edit tools operating on the vault directly |
| Mind (OBn/Khoj) | The index's ingestion pipeline (daily ingest, explicit `upsert_vault_chunk` calls) |
| Spirit (belief-ledger) | Future — reflection pass writes derived beliefs; never raw capture |
| Epigenetics | Read-only within the fleet; we consume, not author |

## Metadata on every write to mind

When an agent does call `mcp__open-brain__capture_thought` or similar, include:

- `source` — slug of the agent/session
- `task_id` — current task or arc
- `agent` — runtime name (hermes / zolivier / kimiclaw / claude)
- `layer` — always `mind` from agent-level writes
- `timestamp` — ISO 8601

## Anti-patterns

- ❌ Duplicate semantic writes — agents writing the same observation N times
- ❌ Unscoped writes — no `source` / no `task_id`
- ❌ Writes to spirit without a reflection pass — spirit entries are derived, never raw
- ❌ Writes to body/mind/spirit *through* tipi — tipi is a view; use the proper channel

## Discovery

Agents read this contract at startup if they want to confirm their behavior matches. File path: `tipi/contract/agent-contract.md`. Version this contract when it changes; record the version number in agent handoffs.
