"""OpenClaw MCP wrapper — dispatch to OLIVIER_MBP (local) or KimiClaw (cloud)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import dispatch_tool_result, run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-openclaw")

    @server.tool()
    def dispatch_to_olivier_mbp(text: str) -> dict[str, Any]:
        """Dispatch to OLIVIER_MBP (local OpenClaw gateway on MacBook Pro, Discord surface Zoe)."""
        return dispatch_tool_result(run_intent("dispatch_olivier_mbp", text=text))

    @server.tool()
    def dispatch_to_kimiclaw(text: str) -> dict[str, Any]:
        """Dispatch to KimiClaw (cloud OpenClaw pod, surfaces Mara/Kopi)."""
        return dispatch_tool_result(run_intent("dispatch_kimiclaw", text=text))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
