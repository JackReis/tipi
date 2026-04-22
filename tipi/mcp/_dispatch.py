"""Shared dispatch engine — reads runtime-dispatch.yaml and runs subprocess.

All MCP runtime wrappers (dizzy, hermes, openclaw, claude_spawn) are thin
shells over `run_intent`. Changing the command for an intent means editing
runtime-dispatch.yaml, never Python.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Location of the canonical dispatch config, relative to this file.
_THIS = Path(__file__).resolve()
DISPATCH_PATH = _THIS.parent.parent / "contract" / "runtime-dispatch.yaml"

def _require_vault_root() -> str:
    """Resolve TIPI_VAULT_ROOT at call time, raise if unset.

    Required — no default. A silent default ties the plugin to one user's
    layout and routes dispatch to the wrong vault for anyone else. Surface
    the config error early instead of mis-routing.
    """
    value = os.environ.get("TIPI_VAULT_ROOT")
    if not value:
        raise DispatchError(
            "TIPI_VAULT_ROOT environment variable is not set. "
            "Set it to the absolute path of your vault (e.g. ~/Documents/=notes)."
        )
    return value


class DispatchError(RuntimeError):
    """Raised when an intent cannot be dispatched (unknown intent, missing
    substitution key, subprocess failure, etc.)."""


@dataclass(frozen=True)
class DispatchResult:
    intent: str
    returncode: int
    stdout: str
    stderr: str
    command: list[str]

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def dispatch_tool_result(result: DispatchResult) -> dict[str, Any]:
    """Standard MCP-tool response shape for every dispatch wrapper.

    Centralizing this means changing the wire format is a one-line diff,
    not a hunt across five wrapper files.
    """
    return {
        "ok": result.ok,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }


def load_dispatch(path: Path = DISPATCH_PATH) -> dict[str, Any]:
    """Load the runtime-dispatch YAML. Small file, no caching needed."""
    if not path.exists():
        raise DispatchError(f"runtime-dispatch.yaml not found at {path}")
    return yaml.safe_load(path.read_text())


def _resolve_command(
    intent: str,
    substitutions: dict[str, str],
    config: dict[str, Any],
) -> list[str]:
    intents = config.get("intents", {})
    if intent not in intents:
        known = ", ".join(sorted(intents.keys()))
        raise DispatchError(f"unknown intent {intent!r}. known: {known}")
    spec = intents[intent]
    if "command" not in spec:
        raise DispatchError(f"intent {intent!r} has no command (transport={spec.get('transport')})")
    command_template: list[str] = spec["command"]
    resolved: list[str] = []
    for token in command_template:
        try:
            resolved.append(token.format_map(substitutions))
        except KeyError as exc:
            missing = exc.args[0]
            raise DispatchError(
                f"intent {intent!r} needs substitution {missing!r}; got {sorted(substitutions)}"
            ) from exc
    return resolved


def run_intent(
    intent: str,
    *,
    runner: Any = None,
    timeout: float | None = 60.0,
    **substitutions: str,
) -> DispatchResult:
    """Resolve and execute an intent.

    `runner` is injectable for tests. Default is None → `subprocess.run`
    looked up *at call time* so monkeypatching `subprocess.run` works.
    `substitutions` are the per-intent {vars}. vault_root defaults to
    TIPI_VAULT_ROOT env var or ~/Documents/=notes.
    """
    if runner is None:
        runner = subprocess.run  # resolved at call time — test-patchable
    substitutions.setdefault("vault_root", _require_vault_root())
    config = load_dispatch()
    command = _resolve_command(intent, substitutions, config)
    completed = runner(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return DispatchResult(
        intent=intent,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        command=command,
    )
