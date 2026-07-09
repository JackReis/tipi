"""Tests for the shared dispatch engine."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

import pytest

from tipi.mcp._dispatch import (
    DispatchError,
    DispatchResult,
    _resolve_command,
    load_dispatch,
    run_intent,
)


@dataclass
class FakeCompleted:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def _fake_runner(**kwargs):
    def runner(cmd, *, capture_output, text, timeout, check):  # noqa: D401
        runner.last_cmd = cmd  # type: ignore[attr-defined]
        return FakeCompleted(**kwargs)

    return runner


def test_load_dispatch_reads_yaml_and_has_expected_intents():
    config = load_dispatch()
    intents = config["intents"]
    for expected in (
        "chat_discord",
        "chat_discord_as_codex",
        "dispatch_hermes",
        "dispatch_olivier_mbp",
        "dispatch_kimiclaw",
        "spawn_claude",
        "dispatch_rbitr",
    ):
        assert expected in intents, f"missing intent: {expected}"


def test_dispatch_rbitr_intent_resolves():
    """@rbitr / dispatch_rbitr resolves to the rbitr HTTP transport on :8765."""
    config = load_dispatch()
    spec = config["intents"]["dispatch_rbitr"]
    assert spec["targets"] == ["rbitr"]
    assert spec["transport"] == "rbitr-http"
    # The inline python command must target port 8765.
    cmd_blob = "\n".join(spec["command"])
    assert "8765" in cmd_blob
    assert "/dispatch" in cmd_blob


def test_resolve_command_substitutes_placeholders():
    config = load_dispatch()
    cmd = _resolve_command(
        "chat_discord",
        {"vault_root": "/tmp/vault", "slug": "zoe", "text": "hello"},
        config,
    )
    assert cmd[0] == "python3"
    assert "--mention" in cmd
    mention_idx = cmd.index("--mention")
    assert cmd[mention_idx + 1] == "zoe"
    assert cmd[-1] == "hello"
    assert "/tmp/vault/claude/scripts/dizzy.py" in cmd


def test_resolve_command_codex_lane_uses_codex_identity():
    config = load_dispatch()
    cmd = _resolve_command(
        "chat_discord_as_codex",
        {"vault_root": "/tmp/vault", "slug": "blue", "text": "hello"},
        config,
    )
    assert cmd[0] == "python3"
    assert "--from" in cmd
    from_idx = cmd.index("--from")
    assert cmd[from_idx + 1] == "codex"
    assert "--tldr" in cmd
    assert cmd[-1] == "hello"
    assert "blue" in cmd


def test_resolve_command_unknown_intent_raises():
    config = load_dispatch()
    with pytest.raises(DispatchError, match="unknown intent"):
        _resolve_command("no_such_intent", {}, config)


def test_resolve_command_missing_substitution_raises():
    config = load_dispatch()
    with pytest.raises(DispatchError, match="needs substitution"):
        _resolve_command(
            "chat_discord",
            {"vault_root": "/tmp", "slug": "zoe"},  # missing 'text'
            config,
        )


def test_run_intent_injects_runner_and_returns_result():
    runner = _fake_runner(returncode=0, stdout="ok", stderr="")
    result = run_intent(
        "chat_discord",
        runner=runner,
        slug="zoe",
        text="hello",
    )
    assert isinstance(result, DispatchResult)
    assert result.ok
    assert result.stdout == "ok"
    assert result.intent == "chat_discord"
    assert "zoe" in result.command
    assert "hello" in result.command


def test_run_intent_codex_lane_uses_codex_dispatch_mode():
    runner = _fake_runner(returncode=0, stdout="ok", stderr="")
    result = run_intent(
        "chat_discord_as_codex",
        runner=runner,
        slug="blue",
        text="hello codex",
    )
    assert isinstance(result, DispatchResult)
    assert result.ok
    assert result.intent == "chat_discord_as_codex"
    assert "--from" in result.command
    assert result.command[result.command.index("--from") + 1] == "codex"
    assert "--tldr" in result.command
    assert "blue" in result.command
    assert "hello codex" in result.command


def test_run_intent_surfaces_nonzero_exit_via_ok_false():
    runner = _fake_runner(returncode=1, stdout="", stderr="boom")
    result = run_intent(
        "spawn_claude",
        runner=runner,
        text="test prompt",
    )
    assert not result.ok
    assert result.returncode == 1
    assert result.stderr == "boom"


def test_run_intent_unknown_intent_raises_before_subprocess():
    runner = _fake_runner()
    with pytest.raises(DispatchError):
        run_intent("frobnicate", runner=runner, text="x")


def test_run_intent_raises_when_vault_root_unset(monkeypatch):
    """TIPI_VAULT_ROOT is required — surface a DispatchError instead of silent mis-route."""
    monkeypatch.delenv("TIPI_VAULT_ROOT", raising=False)
    runner = _fake_runner()
    with pytest.raises(DispatchError, match="TIPI_VAULT_ROOT"):
        run_intent("chat_discord", runner=runner, slug="zoe", text="hello")
