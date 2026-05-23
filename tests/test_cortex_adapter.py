"""Tests for the Cortex adapter.

Requires Cortex running at localhost:8000 with the 'fleet' workspace
populated. If Cortex is unavailable, tests skip gracefully.
"""

from __future__ import annotations

import urllib.error
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tipi.mcp.consciousness.interface import BeliefLedger, MindIndex
from tipi.mcp.cortex.adapter import (
    CortexBeliefLedger,
    CortexMindIndex,
    CortexPeerRegistry,
    _api_call,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cortex_available() -> bool:
    """Probe Cortex health endpoint."""
    try:
        import urllib.request

        with urllib.request.urlopen(
            "http://localhost:8000/api/v1/health", timeout=2
        ):
            return True
    except Exception:
        return False


CORTEX_AVAILABLE = _cortex_available()


# ---------------------------------------------------------------------------
# Unit tests (mocked, no Cortex required)
# ---------------------------------------------------------------------------

class TestApiCall:
    def test_api_call_returns_json_on_success(self):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"status": "healthy"}'

        with patch("tipi.mcp.cortex.adapter.urllib.request.urlopen", return_value=mock_response):
            result = _api_call("GET", "/health")
            assert result == {"status": "healthy"}

    def test_api_call_returns_error_dict_on_http_error(self):
        mock_err = urllib.error.HTTPError(
            "http://localhost/health", 500, "Internal Error", {}, None
        )
        mock_err.read = MagicMock(return_value=b'{"detail": "oops"}')

        with patch("tipi.mcp.cortex.adapter.urllib.request.urlopen", side_effect=mock_err):
            result = _api_call("GET", "/health")
            assert result == {"detail": "oops"}


class TestCortexMindIndexProtocol:
    def test_implements_mind_index(self):
        idx = CortexMindIndex()
        assert isinstance(idx, MindIndex)

    def test_search_returns_list(self):
        with patch("tipi.mcp.cortex.adapter._resolve_workspace_id", return_value="test-ws"):
            with patch("tipi.mcp.cortex.adapter._api_call") as mock_api:
                mock_api.return_value = [
                    {"id": "p1", "name": "neo", "peer_type": "agent"}
                ]
                idx = CortexMindIndex()
                result = idx.search("neo", limit=5)
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0].backend == "cortex"
                assert result[0].content == "Peer: neo (agent)"

    def test_search_falls_back_to_peer_name_match(self):
        with patch("tipi.mcp.cortex.adapter._resolve_workspace_id", return_value="test-ws"):
            with patch("tipi.mcp.cortex.adapter._api_call") as mock_api:
                # Call 1: global search returns nothing usable
                # Call 2: peer list returns peers
                # Call 3: peer-scoped search returns nothing
                # Call 4: peer list again (final fallback name match)
                mock_api.side_effect = [
                    {"results": []},  # global search
                    [{"id": "p1", "name": "neo", "peer_type": "agent"}],  # peer list
                    {"results": []},  # peer-scoped search
                    [{"id": "p1", "name": "neo", "peer_type": "agent"}],  # peer list (fallback)
                ]
                idx = CortexMindIndex()
                result = idx.search("neo", limit=5)
                assert len(result) == 1


class TestCortexBeliefLedgerProtocol:
    def test_implements_belief_ledger(self):
        ledger = CortexBeliefLedger()
        assert isinstance(ledger, BeliefLedger)

    def test_list_beliefs_returns_list(self):
        with patch("tipi.mcp.cortex.adapter._resolve_workspace_id", return_value="test-ws"):
            with patch("tipi.mcp.cortex.adapter._api_call") as mock_api:
                mock_api.side_effect = [
                    [{"id": "p1", "name": "neo"}],  # peers
                    [  # conclusions
                        {
                            "id": "c1",
                            "content": "Neo prefers concise answers",
                            "confidence": 0.85,
                            "session_id": "s1",
                            "created_at": "2026-04-29T12:00:00",
                        }
                    ],
                ]
                ledger = CortexBeliefLedger()
                result = ledger.list_beliefs(limit=5)
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0].claim == "Neo prefers concise answers"
                assert result[0].subjective_weight == 0.85

    def test_search_beliefs_filters_by_query(self):
        with patch("tipi.mcp.cortex.adapter._resolve_workspace_id", return_value="test-ws"):
            with patch("tipi.mcp.cortex.adapter._api_call") as mock_api:
                mock_api.side_effect = [
                    [{"id": "p1", "name": "neo"}],  # peers
                    [  # conclusions
                        {
                            "id": "c1",
                            "content": "Neo prefers concise answers",
                            "confidence": 0.85,
                            "session_id": "s1",
                            "created_at": "2026-04-29T12:00:00",
                        },
                        {
                            "id": "c2",
                            "content": "Codex likes detailed reasoning",
                            "confidence": 0.72,
                            "session_id": "s2",
                            "created_at": "2026-04-29T13:00:00",
                        },
                    ],
                ]
                ledger = CortexBeliefLedger()
                result = ledger.search_beliefs("concise", limit=5)
                assert len(result) == 1
                assert result[0].claim == "Neo prefers concise answers"


class TestCortexPeerRegistry:
    def test_list_peers_returns_list(self):
        with patch("tipi.mcp.cortex.adapter._resolve_workspace_id", return_value="test-ws"):
            with patch("tipi.mcp.cortex.adapter._api_call") as mock_api:
                mock_api.return_value = [
                    {"id": "p1", "name": "neo", "peer_type": "agent"}
                ]
                reg = CortexPeerRegistry()
                result = reg.list_peers()
                assert isinstance(result, list)
                assert result[0]["name"] == "neo"


# ---------------------------------------------------------------------------
# Integration tests (require live Cortex)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not CORTEX_AVAILABLE, reason="Cortex not running on :8000")
class TestCortexIntegration:
    def test_mind_index_search_against_live_cortex(self):
        idx = CortexMindIndex()
        result = idx.search("neo", limit=3)
        assert isinstance(result, list)
        # Should find the 'neo' peer we synced earlier
        names = [r.metadata.get("peer_name", "") for r in result]
        assert "neo" in names or any("neo" in r.content.lower() for r in result)

    def test_belief_ledger_list_against_live_cortex(self):
        ledger = CortexBeliefLedger()
        result = ledger.list_beliefs(limit=5)
        assert isinstance(result, list)
        # May be empty if no conclusions exist yet; that's fine

    def test_peer_registry_against_live_cortex(self):
        reg = CortexPeerRegistry()
        peers = reg.list_peers()
        assert isinstance(peers, list)
        assert len(peers) >= 1  # We synced 9 peers earlier
