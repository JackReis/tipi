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
- `agent` — runtime name (hermes / olivier_mbp / kimiclaw / codex / claude)
- `layer` — always `mind` from agent-level writes
- `timestamp` — ISO 8601

## Anti-patterns

- ❌ Duplicate semantic writes — agents writing the same observation N times
- ❌ Unscoped writes — no `source` / no `task_id`
- ❌ Writes to spirit without a reflection pass — spirit entries are derived, never raw
- ❌ Writes to body/mind/spirit *through* tipi — tipi is a view; use the proper channel
- ❌ Tipi spawning runtimes or injecting cross-agent protocols (e.g. peer-grill) into them — tipi is not a process supervisor and must not carry protocol bodies. Tipi MAY orchestrate wake-signals, rooms, and dropbox paths; runtimes carry the protocol themselves (CC: on-disk skill; API-direct: system-prompt bake referencing the canonical vault doc).
- ❌ Beliefs without producer-side discipline — a `Belief` without `verifier`, `confidence`, or (for contested claims) a `disputation` block is theatre. *An unexamined claim does not exist.*

## Cross-agent protocols

Cross-agent protocols (e.g. `peer-grill` — strict file-only multi-agent reconciliation) are NOT carried by tipi. Tipi may surface the canonical protocol text as a read-only resource, but the runtime invoking the protocol is responsible for knowing how to follow it. Canonical SoT for peer-grill: `~/Documents/=notes/docs/conventions/peer-grill-protocol.md`.

## Belief discipline — dialectic vocabulary

The `Belief` dataclass carries optional dialectic fields for the producer-side discipline. Beliefs are derived (never raw); the dialectic fields are what give a belief enough specificity to be **measured**.

| Field | Purpose | When to populate |
|---|---|---|
| `confidence` | `high` / `medium` / `low` | Always, for any belief crossing session boundaries |
| `verifier` | Runnable `Check` (cmd + expect comparator) | Empirical beliefs whose truth is checkable from filesystem / state |
| `falsifier` | Runnable `Check` that demonstrates the belief is FALSE if it succeeds | Beliefs that would have observable counter-evidence if wrong |
| `disputation` | Scholastic *quaestio* form (`Disputation` type) | High-stakes contested beliefs where the dialectic is load-bearing |
| `aletheia_sha256` | sha256 attestation of the merged statement | Set only when both peers ratify (ἀλήθεια stamp) |

Canonical doctrine: `~/Documents/=notes/docs/conventions/dialectic-vocabulary.md`. **Synthesis:** an unexamined claim does not exist — it's superposition the observer can't collapse. The producer-side discipline gives Beliefs enough specificity to be measured by a downstream reader (or by a peer in `peer-grill` reconciliation).

Sibling consumer-side doctrine: `~/Documents/=notes/docs/conventions/agent-observer-principle.md`. Both rungs collapse to one principle when pushed: a claim is brought into existence by the act of grounding it.

## Discovery

Agents read this contract at startup if they want to confirm their behavior matches. File path: `tipi/contract/agent-contract.md`. Version this contract when it changes; record the version number in agent handoffs.
