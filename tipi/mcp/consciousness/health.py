"""Health fields shared across all enclosures.

These four dataclasses define the wire format for the widget-level health
snapshot the infra-context-dashboard and vs-tipi both render. Field names
are load-bearing — change them here first, propagate everywhere else.

Canonical names agreed in:
    ~/Documents/Coordination/2026-04-21-infra-context-dashboard-coordination.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


Backend = Literal["obn", "khoj", "ob1", "stub"]


@dataclass(frozen=True)
class HandoffFreshness:
    """How fresh is our cross-session coordination signal?"""

    newest_file: str  # relative path from vault root
    age_seconds: int
    count_last_24h: int


@dataclass(frozen=True)
class OB1SyncStatus:
    """Current state of the mind-layer index, whichever backend is live."""

    backend: Backend
    last_sync: str  # ISO 8601
    ok: bool
    record_count: int


@dataclass(frozen=True)
class SessionLock:
    """One lock held on a task in claude/tasks/active/."""

    task_slug: str
    locked_by: str
    lock_acquired: str  # ISO 8601
    age_minutes: int


@dataclass(frozen=True)
class PerSessionMemoryEntry:
    """Per-session breakdown of the vault-native project_memory.json."""

    session_id: str
    count: int
    approaching_consolidation: bool


@dataclass(frozen=True)
class ProjectMemoryEntries:
    """Top-level shape for project_memory.json health."""

    total: int
    limit: int
    per_session: tuple[PerSessionMemoryEntry, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HealthSnapshot:
    """Composite — one poll of all four health fields at once."""

    handoff_freshness: HandoffFreshness
    ob1_sync_status: OB1SyncStatus
    session_lock_state: tuple[SessionLock, ...]
    project_memory_entries: ProjectMemoryEntries


@runtime_checkable
class HealthReader(Protocol):
    """Read surface for the composite health snapshot."""

    def snapshot(self) -> HealthSnapshot: ...
