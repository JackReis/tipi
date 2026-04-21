"""Consciousness interface — the integration seam between tipi and the three layers.

This module defines the SOURCE of truth for the shared consciousness contract.
The JSON Schema shipped in `tipi/contract/consciousness-interface.json` (future
plan Task 9.2) is generated from these definitions.

See the vault ADR at `~/Documents/=notes/docs/architecture/three-layer-consciousness.md`
for the architecture rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Spirit layer — beliefs from the future OB1 belief-ledger
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Belief:
    """A durable, subjectively-weighted claim in the belief ledger.

    Beliefs are derived — never raw captures. A write to spirit implies a
    reflection pass over mind.
    """

    id: str
    claim: str
    subjective_weight: float  # 0.0 - 1.0
    derived_from: tuple[str, ...] = ()  # mind-layer record IDs
    timestamp: str = ""  # ISO 8601


@runtime_checkable
class BeliefLedger(Protocol):
    """Read surface over the spirit layer."""

    def list_beliefs(self, limit: int = 20) -> list[Belief]: ...
    def search_beliefs(self, query: str, limit: int = 5) -> list[Belief]: ...


# ---------------------------------------------------------------------------
# Mind layer — knowledge records from OBn / Khoj / knowledge-graph
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MindRecord:
    """A retrieval hit from the mind layer (backend-agnostic).

    `backend` discriminates the source: obn | khoj | knowledge-graph | ...
    """

    id: str
    content: str
    score: float
    backend: str = "obn"
    metadata: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class MindIndex(Protocol):
    """Read surface over the mind layer. Implementation may back to OBn or Khoj."""

    def search(self, query: str, limit: int = 10) -> list[MindRecord]: ...


# ---------------------------------------------------------------------------
# Body layer — the neural-garden vault + sibling repos + OS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BodyState:
    """Snapshot of the body substrate."""

    repos: tuple[str, ...] = ()
    recent_changes: tuple[dict[str, str], ...] = ()


@runtime_checkable
class BodyReader(Protocol):
    """Read surface over the body layer."""

    def list_repos(self) -> list[str]: ...
    def recent_changes(self, repo: str, limit: int = 5) -> list[dict[str, str]]: ...
