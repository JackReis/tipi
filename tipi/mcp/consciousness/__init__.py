"""Consciousness MCP — reads body / mind / spirit + shared health through stable interfaces."""
from tipi.mcp.consciousness.health import (
    HandoffFreshness,
    HealthReader,
    HealthSnapshot,
    OB1SyncStatus,
    PerSessionMemoryEntry,
    ProjectMemoryEntries,
    SessionLock,
)
from tipi.mcp.consciousness.interface import (
    Belief,
    BodyState,
    MindRecord,
    BeliefLedger,
    MindIndex,
    BodyReader,
)

__all__ = [
    # interface
    "Belief",
    "BodyState",
    "MindRecord",
    "BeliefLedger",
    "MindIndex",
    "BodyReader",
    # health
    "HandoffFreshness",
    "OB1SyncStatus",
    "SessionLock",
    "PerSessionMemoryEntry",
    "ProjectMemoryEntries",
    "HealthSnapshot",
    "HealthReader",
]
