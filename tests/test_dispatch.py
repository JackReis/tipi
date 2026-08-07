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
    resolve_intent_alias,
    run_intent,
)


@dataclass
class FakeCompleted:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""

    def __getattr__(self, name):
        return ""
    def __getitem__(self, key):
        return ""


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
        "dispatch_arbiter",
        "dispatch_rbitr",
        "dispatch_ringside",
    ):
        assert expected in intents, f"missing intent: {expected}"


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
    with pytest.raises(DispatchError, match="unknown intent") as exc_info:
        _resolve_command("no_such_intent", {}, config)
    assert "dispatch_rbitr" in str(exc_info.value)


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


# ---------------------------------------------------------------------------
# dispatch_ringside intent tests
# ---------------------------------------------------------------------------

def test_dispatch_ringside_intent_registered_with_correct_metadata():
    """dispatch_ringside targets the Ringside visibility surface on :8700."""
    config = load_dispatch()
    spec = config["intents"]["dispatch_ringside"]
    assert spec["targets"] == ["ringside"]
    assert spec["transport"] == "ringside-http"
    assert spec["description"], "intent should have a description"


def test_dispatch_ringside_command_resolves_with_text_substitution():
    """dispatch_ringside command template resolves {text} and references :8700.

    Previously the inline Python f-string braces caused format_map to fail.
    Those braces are now escaped (doubled) so only {text} is substituted.
    """
    config = load_dispatch()
    cmd = _resolve_command(
        "dispatch_ringside",
        {"vault_root": "/tmp/vault", "text": "ringside test"},
        config,
    )
    assert cmd[0] == "python3"
    assert cmd[-1] == "ringside test"
    assert any("8700" in str(c) for c in cmd)


# ---------------------------------------------------------------------------
# dispatch_rbitr intent tests
# ---------------------------------------------------------------------------

def test_dispatch_rbitr_intent_registered_with_correct_metadata():
    """dispatch_rbitr targets the Rbitr orchestrator on :8765."""
    config = load_dispatch()
    spec = config["intents"]["dispatch_rbitr"]
    assert spec["targets"] == ["rbitr"]
    assert spec["transport"] == "rbitr-http"
    assert spec["description"], "intent should have a description"


def test_dispatch_rbitr_command_resolves_with_text_substitution():
    """dispatch_rbitr command template resolves {text} and references :8765.

    Previously the inline Python f-string braces caused format_map to fail.
    Those braces are now escaped (doubled) so only {text} is substituted.
    """
    config = load_dispatch()
    cmd = _resolve_command(
        "dispatch_rbitr",
        {"vault_root": "/tmp/vault", "text": "hello rbitr"},
        config,
    )
    assert cmd[0] == "python3"
    assert cmd[-1] == "hello rbitr"
    assert any("8765" in str(c) for c in cmd)


def test_dispatch_arbiter_command_still_resolves():
    """dispatch_arbiter (backward compat) also resolves after brace escaping."""
    config = load_dispatch()
    cmd = _resolve_command(
        "dispatch_arbiter",
        {"vault_root": "/tmp/vault", "text": "arbiter test"},
        config,
    )
    assert cmd[0] == "python3"
    assert cmd[-1] == "arbiter test"
    assert any("8765" in str(c) for c in cmd)


# ---------------------------------------------------------------------------
# Intent alias resolution tests (vs-tipi @-shortname support)
# ---------------------------------------------------------------------------

def test_resolve_intent_alias_passes_through_known_intent_name():
    """A fully-qualified intent name passes through unchanged."""
    config = load_dispatch()
    assert resolve_intent_alias("dispatch_rbitr", config) == "dispatch_rbitr"
    assert resolve_intent_alias("dispatch_ringside", config) == "dispatch_ringside"
    assert resolve_intent_alias("dispatch_hermes", config) == "dispatch_hermes"


def test_resolve_intent_alias_at_rbitr_resolves_to_dispatch_rbitr():
    """vs-tipi resolves @rbitr to the dispatch_rbitr intent."""
    config = load_dispatch()
    result = resolve_intent_alias("@rbitr", config)
    assert result == "dispatch_rbitr"


def test_resolve_intent_alias_at_ringside_resolves_to_dispatch_ringside():
    """vs-tipi resolves @ringside to the dispatch_ringside intent."""
    config = load_dispatch()
    result = resolve_intent_alias("@ringside", config)
    assert result == "dispatch_ringside"


def test_resolve_intent_alias_at_hermes_resolves_to_dispatch_hermes():
    """vs-tipi resolves @hermes to the dispatch_hermes intent."""
    config = load_dispatch()
    result = resolve_intent_alias("@hermes", config)
    assert result == "dispatch_hermes"


def test_resolve_intent_alias_at_codex_resolves_to_chat_discord_as_codex():
    """@codex resolves via target matching to chat_discord_as_codex."""
    config = load_dispatch()
    result = resolve_intent_alias("@codex", config)
    assert result == "chat_discord_as_codex"


def test_resolve_intent_alias_unknown_raises_with_known_list():
    """Unknown aliases raise DispatchError listing known intents."""
    config = load_dispatch()
    with pytest.raises(DispatchError, match="cannot resolve intent alias"):
        resolve_intent_alias("@nonexistent", config)


def test_resolve_intent_alias_without_at_does_not_match():
    """A bare name without @ prefix that isn't an intent raises."""
    config = load_dispatch()
    with pytest.raises(DispatchError, match="cannot resolve"):
        resolve_intent_alias("rbitr", config)


def test_run_intent_accepts_at_alias():
    """run_intent accepts @-shortnames and resolves them before dispatch."""
    config = load_dispatch()
    runner = _fake_runner(returncode=0, stdout="ok", stderr="")
    result = run_intent(
        "@rbitr",
        runner=runner,
        text="alias dispatch test",
    )
    assert result.ok
    assert result.intent == "dispatch_rbitr"
    assert "hello" not in result.command  # sanity — no stray values
    assert "alias dispatch test" in result.command
    assert any("8765" in str(c) for c in result.command)


def test_run_intent_accepts_at_ringside_alias():
    """run_intent accepts @ringside alias and resolves to dispatch_ringside."""
    runner = _fake_runner(returncode=0, stdout="ok", stderr="")
    result = run_intent(
        "@ringside",
        runner=runner,
        text="visualize fleet",
    )
    assert result.ok
    assert result.intent == "dispatch_ringside"
    assert "visualize fleet" in result.command
    assert any("8700" in str(c) for c in result.command)
