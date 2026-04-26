"""Tests for the thin runtime MCP wrappers.

Each wrapper's server builds cleanly and registers the expected tools.
Subprocess is mocked via the dispatch engine's runner injection so tests
never touch the real CLIs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from tipi.mcp import _dispatch
from tipi.mcp.claude_spawn.server import build_server as build_claude_spawn
from tipi.mcp.dizzy.server import build_server as build_dizzy
from tipi.mcp.hermes.server import build_server as build_hermes
from tipi.mcp.openclaw.server import build_server as build_openclaw


@dataclass
class FakeCompleted:
    returncode: int = 0
    stdout: str = "mock-ok"
    stderr: str = ""


@pytest.fixture
def fake_runner(monkeypatch):
    calls: list[list[str]] = []

    def runner(cmd, *, capture_output, text, timeout, check):
        calls.append(cmd)
        return FakeCompleted()

    # Patch subprocess.run at the dispatch-engine boundary so every wrapper
    # inherits the fake without per-test boilerplate.
    monkeypatch.setattr(_dispatch.subprocess, "run", runner)
    return calls


# ---------------------------------------------------------------------------
# Each wrapper builds + registers expected tools
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "builder, name, expected_tools",
    [
        (build_dizzy, "tipi-dizzy", {"send_to_discord", "send_to_discord_as_codex"}),
        (build_hermes, "tipi-hermes", {"dispatch_to_hermes"}),
        (build_openclaw, "tipi-openclaw", {"dispatch_to_olivier_mbp", "dispatch_to_kimiclaw"}),
        (build_claude_spawn, "tipi-claude-spawn", {"spawn_claude_session"}),
    ],
)
def test_wrapper_builds_and_registers_tools(builder, name, expected_tools):
    server = builder()
    assert server.name == name
    tools = asyncio.run(server.list_tools())
    registered = {t.name for t in tools}
    assert expected_tools.issubset(registered), f"missing: {expected_tools - registered}"


# ---------------------------------------------------------------------------
# Wrappers shell out via the dispatch engine
# ---------------------------------------------------------------------------

async def _call(server, name, args):
    result = await server.call_tool(name, args)
    if isinstance(result, tuple) and len(result) == 2:
        return result[1]  # structured
    return result


def _unwrap(result):
    """Unwrap FastMCP's structured_content envelope."""
    return result.get("result", result) if isinstance(result, dict) else result


def test_dizzy_send_resolves_command_with_mention(fake_runner):
    server = build_dizzy()
    result = asyncio.run(_call(server, "send_to_discord", {"mention": "zoe", "text": "ping"}))
    data = _unwrap(result)
    assert data["ok"] is True
    assert data["stdout"] == "mock-ok"
    assert len(fake_runner) == 1
    cmd = fake_runner[0]
    assert "zoe" in cmd
    assert "ping" in cmd
    assert "--mention" in cmd


def test_dizzy_codex_send_uses_codex_lane(fake_runner):
    server = build_dizzy()
    result = asyncio.run(
        _call(server, "send_to_discord_as_codex", {"mention": "blue", "text": "ping codex"})
    )
    data = _unwrap(result)
    assert data["ok"] is True
    assert data["stdout"] == "mock-ok"
    assert len(fake_runner) == 1
    cmd = fake_runner[0]
    assert "blue" in cmd
    assert "ping codex" in cmd
    assert "--from" in cmd
    from_idx = cmd.index("--from")
    assert cmd[from_idx + 1] == "codex"
    assert "--tldr" in cmd


def test_hermes_dispatch_builds_hermes_command(fake_runner):
    server = build_hermes()
    asyncio.run(_call(server, "dispatch_to_hermes", {"text": "hello hermes"}))
    cmd = fake_runner[0]
    assert cmd[0] == "hermes"
    assert "hello hermes" in cmd


def test_openclaw_olivier_mbp_and_kimiclaw_differ(fake_runner):
    server = build_openclaw()
    asyncio.run(_call(server, "dispatch_to_olivier_mbp", {"text": "local"}))
    asyncio.run(_call(server, "dispatch_to_kimiclaw", {"text": "cloud"}))
    assert len(fake_runner) == 2
    local_cmd, cloud_cmd = fake_runner
    assert "--remote" not in local_cmd
    assert "--remote" in cloud_cmd


def test_claude_spawn_uses_dangerous_flag(fake_runner):
    server = build_claude_spawn()
    asyncio.run(_call(server, "spawn_claude_session", {"text": "test prompt"}))
    cmd = fake_runner[0]
    assert cmd[0] == "claude"
    assert "--dangerously-skip-permissions" in cmd


def test_wrappers_return_standard_shape(fake_runner):
    """Every dispatch wrapper returns {ok, returncode, stdout, stderr, command}."""
    server = build_dizzy()
    result = asyncio.run(_call(server, "send_to_discord", {"mention": "zoe", "text": "x"}))
    data = _unwrap(result)
    assert set(data.keys()) == {"ok", "returncode", "stdout", "stderr", "command"}
