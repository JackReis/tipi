"""claude_spawn MCP wrapper — spawn a fresh Claude Code session.

Equivalent of `claude --dangerously-skip-permissions "<prompt>"`. Use sparingly:
spawns a new session, burns tokens, doesn't reach back into the caller's session.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import dispatch_tool_result, run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-claude-spawn")

    @server.tool()
    def spawn_claude_session(text: str) -> dict[str, Any]:
        """Spawn a fresh Claude Code session with the given prompt.

        Blocks until the spawned session exits (or the 60s timeout trips).
        Use when you want to initiate a parallel worker rather than continue
        the task in the current session.
        """
        return dispatch_tool_result(run_intent("spawn_claude", text=text))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
