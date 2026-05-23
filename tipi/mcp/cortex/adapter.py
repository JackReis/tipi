"""Cortex adapter — tipi consciousness interface over Cortex (Honcho-local) API.

Implements:
- MindIndex   → Cortex peer search + session context
- BeliefLedger → Cortex peer conclusions (read-only)

Cortex runs at http://localhost:8000/api/v1.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from tipi.mcp.consciousness.interface import (
    Belief,
    BeliefLedger,
    MindIndex,
    MindRecord,
)

CORTEX_API = "http://localhost:8000/api/v1"
DEFAULT_WORKSPACE_NAME = "fleet"


def _resolve_workspace_id(name: str = DEFAULT_WORKSPACE_NAME) -> str:
    """Look up workspace ID by name. Cortex uses nanoid IDs, not names."""
    result = _api_call("POST", "/workspaces", {})
    workspaces = result if isinstance(result, list) else []
    for ws in workspaces:
        if ws.get("name") == name:
            return ws["id"]
    # Fallback: return the name itself and let the API fail visibly
    return name


def _api_call(method: str, path: str, data: dict[str, Any] | None = None) -> Any:
    """Minimal HTTP client for Cortex."""
    url = f"{CORTEX_API}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        err = exc.read().decode()
        try:
            return json.loads(err)
        except json.JSONDecodeError:
            return {"error": err}
    except Exception as exc:
        return {"error": str(exc)}


class CortexMindIndex(MindIndex):
    """Mind-layer read surface backed by Cortex search + peer context."""

    def __init__(self, workspace_name: str = DEFAULT_WORKSPACE_NAME) -> None:
        self.workspace_id = _resolve_workspace_id(workspace_name)

    # ------------------------------------------------------------------
    # MindIndex protocol
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[MindRecord]:
        """Search across Cortex peers, sessions, and messages."""
        records: list[MindRecord] = []

        # 1. Global Cortex search (if available)
        search_result = _api_call(
            "POST",
            "/search",
            {"query": query, "limit": limit},
        )
        if isinstance(search_result, dict) and "results" in search_result:
            for hit in search_result["results"][:limit]:
                records.append(
                    MindRecord(
                        id=hit.get("id", "unknown"),
                        content=hit.get("content", ""),
                        score=hit.get("score", 0.0),
                        backend="cortex",
                        metadata={
                            "type": hit.get("type", "unknown"),
                            "workspace_id": self.workspace_id,
                        },
                    )
                )

        # 2. If global search returned nothing or is unavailable,
        #    fall back to peer-scoped search across all peers.
        if not records:
            peers = _api_call("POST", f"/peers?workspace_id={self.workspace_id}", {})
            if isinstance(peers, list):
                for peer in peers[:limit]:
                    peer_id = peer.get("id")
                    if not peer_id:
                        continue
                    peer_search = _api_call(
                        "POST",
                        f"/peers/{peer_id}/search",
                        {"query": query, "limit": 3},
                    )
                    if isinstance(peer_search, dict) and "results" in peer_search:
                        for hit in peer_search["results"][:3]:
                            records.append(
                                MindRecord(
                                    id=hit.get("id", "unknown"),
                                    content=hit.get("content", ""),
                                    score=hit.get("score", 0.0),
                                    backend="cortex",
                                    metadata={
                                        "peer_id": peer_id,
                                        "peer_name": peer.get("name", "unknown"),
                                        "type": hit.get("type", "unknown"),
                                    },
                                )
                            )
                    if len(records) >= limit:
                        break

        # 3. Final fallback: match peer names directly
        if not records:
            peers = _api_call("POST", f"/peers?workspace_id={self.workspace_id}", {})
            if isinstance(peers, list):
                for peer in peers:
                    name = peer.get("name", "").lower()
                    if query.lower() in name:
                        records.append(
                            MindRecord(
                                id=peer.get("id", "unknown"),
                                content=f"Peer: {peer.get('name', 'unknown')} ({peer.get('peer_type', 'unknown')})",
                                score=1.0,
                                backend="cortex",
                                metadata={
                                    "peer_id": peer.get("id"),
                                    "type": "peer",
                                },
                            )
                        )
                    if len(records) >= limit:
                        break

        return records[:limit]


class CortexBeliefLedger(BeliefLedger):
    """Spirit-layer read surface backed by Cortex peer conclusions.

    Cortex conclusions are derived facts from session analysis.
    They map naturally to tipi Beliefs (durable, derived claims).
    """

    def __init__(self, workspace_name: str = DEFAULT_WORKSPACE_NAME) -> None:
        self.workspace_id = _resolve_workspace_id(workspace_name)

    # ------------------------------------------------------------------
    # BeliefLedger protocol
    # ------------------------------------------------------------------

    def list_beliefs(self, limit: int = 20) -> list[Belief]:
        """Aggregate conclusions across all peers in the workspace."""
        beliefs: list[Belief] = []
        peers = _api_call("POST", f"/peers?workspace_id={self.workspace_id}", {})
        if not isinstance(peers, list):
            return beliefs

        for peer in peers:
            peer_id = peer.get("id")
            if not peer_id:
                continue
            conclusions = _api_call("GET", f"/peers/{peer_id}/conclusions")
            if isinstance(conclusions, list):
                for conclusion in conclusions[:5]:  # cap per peer
                    beliefs.append(
                        Belief(
                            id=conclusion.get("id", f"{peer_id}-unknown"),
                            claim=conclusion.get("content", ""),
                            subjective_weight=conclusion.get("confidence", 0.5),
                            derived_from=(conclusion.get("session_id", ""),),
                            timestamp=conclusion.get("created_at", ""),
                        )
                    )
            if len(beliefs) >= limit:
                break

        return beliefs[:limit]

    def search_beliefs(self, query: str, limit: int = 5) -> list[Belief]:
        """Search conclusions by content match."""
        beliefs: list[Belief] = []
        peers = _api_call("POST", f"/peers?workspace_id={self.workspace_id}", {})
        if not isinstance(peers, list):
            return beliefs

        for peer in peers:
            peer_id = peer.get("id")
            if not peer_id:
                continue
            conclusions = _api_call("GET", f"/peers/{peer_id}/conclusions")
            if isinstance(conclusions, list):
                for conclusion in conclusions:
                    content = conclusion.get("content", "")
                    if query.lower() in content.lower():
                        beliefs.append(
                            Belief(
                                id=conclusion.get("id", f"{peer_id}-unknown"),
                                claim=content,
                                subjective_weight=conclusion.get("confidence", 0.5),
                                derived_from=(conclusion.get("session_id", ""),),
                                timestamp=conclusion.get("created_at", ""),
                            )
                        )
                    if len(beliefs) >= limit:
                        break
            if len(beliefs) >= limit:
                break

        return beliefs[:limit]


class CortexPeerRegistry:
    """Body-layer read surface for fleet peer metadata.

    Not yet a tipi protocol, but provides the substrate registry
    that body-layer tools need to know *who* is in the fleet.
    """

    def __init__(self, workspace_name: str = DEFAULT_WORKSPACE_NAME) -> None:
        self.workspace_id = _resolve_workspace_id(workspace_name)

    def list_peers(self) -> list[dict[str, Any]]:
        result = _api_call("POST", f"/peers?workspace_id={self.workspace_id}", {})
        return result if isinstance(result, list) else []

    def peer_metadata(self, peer_id: str) -> dict[str, Any]:
        """Return peer card + representation as unified metadata."""
        card = _api_call("GET", f"/peers/{peer_id}/card")
        rep = _api_call("GET", f"/peers/{peer_id}/representation")
        return {
            "card": card if isinstance(card, dict) else {},
            "representation": rep if isinstance(rep, dict) else {},
        }
