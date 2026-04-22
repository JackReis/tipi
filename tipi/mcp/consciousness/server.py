"""Consciousness MCP server — exposes body/mind/spirit stubs as MCP tools.

Boots against `tipi.mcp.consciousness.stubs` by default. Swap to real
implementations by changing the three CONSCIOUSNESS_* instantiations below
(or via env-var injection — future work).

Run:
    python -m tipi.mcp.consciousness.server

Smoke-test (from Python):
    from tipi.mcp.consciousness.server import build_server
    server = build_server()
    tools = server.list_tools_sync()  # returns tool metadata for verification
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp.consciousness.stubs import (
    StubBeliefLedger,
    StubBodyReader,
    StubHealthReader,
    StubMindIndex,
    body_state_snapshot,
)

# Wire the stubs. To swap to real backends, change these lines.
BELIEF_LEDGER = StubBeliefLedger()
MIND_INDEX = StubMindIndex()
BODY_READER = StubBodyReader()
HEALTH_READER = StubHealthReader()


def build_server() -> FastMCP:
    """Build and return the FastMCP server. Keeping this factored out so
    tests can introspect it without starting a stdio loop."""

    server = FastMCP("tipi-consciousness")

    @server.tool()
    def list_beliefs(limit: int = 20) -> list[dict[str, Any]]:
        """Return beliefs from the spirit layer (list form, newest first)."""
        return [asdict(b) for b in BELIEF_LEDGER.list_beliefs(limit=limit)]

    @server.tool()
    def search_beliefs(query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search the belief ledger by claim text (substring match)."""
        return [asdict(b) for b in BELIEF_LEDGER.search_beliefs(query=query, limit=limit)]

    @server.tool()
    def search_mind(query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the mind layer (OBn/Khoj/stub) for records matching the query."""
        return [asdict(r) for r in MIND_INDEX.search(query=query, limit=limit)]

    @server.tool()
    def list_repos() -> list[str]:
        """List repos the body layer knows about."""
        return BODY_READER.list_repos()

    @server.tool()
    def recent_changes(repo: str, limit: int = 5) -> list[dict[str, str]]:
        """Return recent changes for a body-layer repo."""
        return BODY_READER.recent_changes(repo=repo, limit=limit)

    @server.tool()
    def body_state() -> dict[str, Any]:
        """Return a snapshot of the body substrate state."""
        snap = body_state_snapshot()
        return {
            "repos": list(snap.repos),
            "recent_changes": list(snap.recent_changes),
        }

    @server.tool()
    def health_snapshot() -> dict[str, Any]:
        """Return the composite cross-layer health snapshot.

        Shape matches `tipi/contract/consciousness-interface.json`. Consumed
        by the infra-context-dashboard (Task B10) and the vs-tipi Today
        chat mode (health chip row).
        """
        snap = HEALTH_READER.snapshot()
        return {
            "handoff_freshness": asdict(snap.handoff_freshness),
            "ob1_sync_status": asdict(snap.ob1_sync_status),
            "session_lock_state": [asdict(s) for s in snap.session_lock_state],
            "project_memory_entries": asdict(snap.project_memory_entries),
        }

    return server


def main() -> None:
    """Entry point for `python -m tipi.mcp.consciousness.server`."""
    server = build_server()
    server.run()  # stdio transport by default


if __name__ == "__main__":
    main()
