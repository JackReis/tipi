"""Deterministic stubs for the consciousness interfaces.

Lets tipi boot before the real body/mind/spirit backends exist. Swap in real
implementations without changing the interface contract.
"""

from __future__ import annotations

from tipi.mcp.consciousness.interface import (
    Belief,
    BodyReader,
    BodyState,
    BeliefLedger,
    MindIndex,
    MindRecord,
)


class StubBeliefLedger(BeliefLedger):
    _FIXTURES: tuple[Belief, ...] = (
        Belief(
            id="belief-001",
            claim="The vault is the single source of truth.",
            subjective_weight=0.95,
            derived_from=("memory-MEMORY.md",),
            timestamp="2026-04-21T00:00:00Z",
        ),
        Belief(
            id="belief-002",
            claim="Coordination folder is an un-gitted scratchpad.",
            subjective_weight=0.80,
            derived_from=("conventions-multi-session-working-agreements",),
            timestamp="2026-04-21T00:00:00Z",
        ),
    )

    def list_beliefs(self, limit: int = 20) -> list[Belief]:
        return list(self._FIXTURES[:limit])

    def search_beliefs(self, query: str, limit: int = 5) -> list[Belief]:
        q = query.lower()
        hits = [b for b in self._FIXTURES if q in b.claim.lower()]
        return hits[:limit]


class StubMindIndex(MindIndex):
    _FIXTURES: tuple[MindRecord, ...] = (
        MindRecord(
            id="mind-001",
            content="Tipi is a portable fleet core — poles + cover; enclosures pick location.",
            score=0.9,
            backend="stub",
        ),
    )

    def search(self, query: str, limit: int = 10) -> list[MindRecord]:
        q = query.lower()
        hits = [m for m in self._FIXTURES if q in m.content.lower()]
        return hits[:limit]


class StubBodyReader(BodyReader):
    _REPOS = ("=notes", "tipi", "vs-tipi")

    def list_repos(self) -> list[str]:
        return list(self._REPOS)

    def recent_changes(self, repo: str, limit: int = 5) -> list[dict[str, str]]:
        return [
            {"repo": repo, "commit": "stub-sha-0001", "message": "stub change"}
            for _ in range(min(limit, 1))
        ]


def body_state_snapshot() -> BodyState:
    reader = StubBodyReader()
    return BodyState(
        repos=tuple(reader.list_repos()),
        recent_changes=tuple(reader.recent_changes(repo="=notes", limit=1)),
    )
