"""dizzy MCP wrapper — Discord fleet chatter via claude/scripts/dizzy.py.

Exposes one tool: `send_to_discord(mention, text)`. Under the hood, resolves
the `chat_discord` intent in runtime-dispatch.yaml and shells out.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-dizzy")

    @server.tool()
    def send_to_discord(mention: str, text: str) -> dict[str, Any]:
        """Send a message to Discord #bots, @-mentioning `mention` (e.g. 'zoe', 'mara').

        Returns the subprocess outcome: returncode, stdout, stderr, resolved command.
        """
        result = run_intent("chat_discord", slug=mention, text=text)
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
