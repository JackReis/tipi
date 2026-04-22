"""claude_spawn MCP wrapper — spawn a fresh Claude Code session.

Equivalent of `claude --dangerously-skip-permissions "<prompt>"`.
Use sparingly — spawns a new session, burns tokens, doesn't reach back
into the caller's session. For reaching THIS running session, see the
`reach_running_session` intent (telegram-bridge).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-claude-spawn")

    @server.tool()
    def spawn_claude_session(text: str) -> dict[str, Any]:
        """Spawn a fresh Claude Code session with the given prompt.

        The spawned session runs independently; this tool blocks until it
        exits (or the 60s timeout trips). Most useful when you want the
        current agent to initiate a parallel worker rather than continue
        the task itself.
        """
        result = run_intent("spawn_claude", text=text)
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": result.command,
        }

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
