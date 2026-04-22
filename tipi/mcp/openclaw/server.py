"""OpenClaw MCP wrapper — dispatch to Zolivier (local) or KimiClaw (cloud).

Exposes two tools that map to the two OpenClaw intents in runtime-dispatch.yaml.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-openclaw")

    @server.tool()
    def dispatch_to_zolivier(text: str) -> dict[str, Any]:
        """Dispatch to Zolivier (local OpenClaw gateway, Discord surface Zoe)."""
        result = run_intent("dispatch_zolivier", text=text)
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": result.command,
        }

    @server.tool()
    def dispatch_to_kimiclaw(text: str) -> dict[str, Any]:
        """Dispatch to KimiClaw (cloud OpenClaw pod, surfaces Mara/Kopi)."""
        result = run_intent("dispatch_kimiclaw", text=text)
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
