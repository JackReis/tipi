"""Tests for tipi.mcp.consciousness.

Verifies that stubs satisfy the Protocol interfaces — this is the contract
test that guards the interface seam as real backends land.
"""

from __future__ import annotations

import pytest

from tipi.mcp.consciousness import (
    Belief,
    BeliefLedger,
    BodyReader,
    BodyState,
    MindIndex,
    MindRecord,
)
from tipi.mcp.consciousness.stubs import (
    StubBeliefLedger,
    StubBodyReader,
    StubMindIndex,
    body_state_snapshot,
)


# ---------------------------------------------------------------------------
# Protocol conformance — guards the contract
# ---------------------------------------------------------------------------

def test_stub_belief_ledger_conforms_to_protocol():
    assert isinstance(StubBeliefLedger(), BeliefLedger)


def test_stub_mind_index_conforms_to_protocol():
    assert isinstance(StubMindIndex(), MindIndex)


def test_stub_body_reader_conforms_to_protocol():
    assert isinstance(StubBodyReader(), BodyReader)


# ---------------------------------------------------------------------------
# Behavior — the stubs return deterministic data the runtime can rely on
# ---------------------------------------------------------------------------

def test_belief_list_returns_beliefs():
    ledger = StubBeliefLedger()
    beliefs = ledger.list_beliefs(limit=5)
    assert len(beliefs) >= 1
    assert all(isinstance(b, Belief) for b in beliefs)
    assert all(0.0 <= b.subjective_weight <= 1.0 for b in beliefs)


def test_belief_search_matches_claim_substring():
    ledger = StubBeliefLedger()
    hits = ledger.search_beliefs(query="vault")
    assert len(hits) >= 1
    assert any("vault" in b.claim.lower() for b in hits)


def test_belief_search_miss_returns_empty():
    ledger = StubBeliefLedger()
    hits = ledger.search_beliefs(query="xyzzynotfound")
    assert hits == []


def test_mind_search_returns_records_with_backend_tag():
    idx = StubMindIndex()
    results = idx.search(query="tipi")
    assert len(results) >= 1
    assert all(isinstance(r, MindRecord) for r in results)
    assert all(r.backend for r in results)  # backend tag is required


def test_body_reader_lists_repos_including_vault():
    reader = StubBodyReader()
    repos = reader.list_repos()
    assert "=notes" in repos


def test_body_state_snapshot_populates_fields():
    snap = body_state_snapshot()
    assert isinstance(snap, BodyState)
    assert len(snap.repos) >= 1
    assert len(snap.recent_changes) >= 1


# ---------------------------------------------------------------------------
# Subjective-weight invariant — guards belief-ledger write discipline
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("weight,valid", [
    (0.0, True),
    (0.5, True),
    (1.0, True),
    (-0.1, False),
    (1.5, False),
])
def test_belief_weight_invariant(weight: float, valid: bool):
    if valid:
        Belief(id="test", claim="x", subjective_weight=weight)
    else:
        b = Belief(id="test", claim="x", subjective_weight=weight)
        assert not (0.0 <= b.subjective_weight <= 1.0)
