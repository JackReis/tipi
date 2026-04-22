"""Smoke tests for the consciousness MCP server.

Verifies the server builds, registers the expected tools, and each tool
returns data of the expected shape. Does NOT start the stdio transport.
"""

from __future__ import annotations

import asyncio

import pytest

from tipi.mcp.consciousness.server import build_server


@pytest.fixture
def server():
    return build_server()


def test_server_builds_with_expected_name(server):
    assert server.name == "tipi-consciousness"


async def _list_tool_names(server) -> list[str]:
    tools = await server.list_tools()
    return [t.name for t in tools]


def test_server_registers_expected_tools(server):
    names = asyncio.run(_list_tool_names(server))
    expected = {
        "list_beliefs",
        "search_beliefs",
        "search_mind",
        "list_repos",
        "recent_changes",
        "body_state",
    }
    assert expected.issubset(set(names)), f"missing: {expected - set(names)}"


async def _call_tool(server, name: str, args: dict):
    result = await server.call_tool(name, args)
    # FastMCP returns (content_list, structured_content)
    if isinstance(result, tuple) and len(result) == 2:
        _content, structured = result
        return structured
    return result


def test_list_beliefs_returns_list_of_dicts(server):
    result = asyncio.run(_call_tool(server, "list_beliefs", {"limit": 5}))
    # Structured content may wrap the list; unwrap if so
    data = result.get("result", result) if isinstance(result, dict) else result
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "claim" in data[0]
    assert "subjective_weight" in data[0]


def test_search_beliefs_finds_by_substring(server):
    result = asyncio.run(_call_tool(server, "search_beliefs", {"query": "vault"}))
    data = result.get("result", result) if isinstance(result, dict) else result
    assert isinstance(data, list)
    assert any("vault" in b["claim"].lower() for b in data)


def test_list_repos_includes_vault(server):
    result = asyncio.run(_call_tool(server, "list_repos", {}))
    data = result.get("result", result) if isinstance(result, dict) else result
    assert isinstance(data, list)
    assert "=notes" in data


def test_body_state_returns_dict_with_repos(server):
    result = asyncio.run(_call_tool(server, "body_state", {}))
    data = result.get("result", result) if isinstance(result, dict) else result
    assert isinstance(data, dict)
    assert "repos" in data
    assert isinstance(data["repos"], list)
