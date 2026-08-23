"""Rbitr MCP wrapper — dispatch task to the local Rbitr orchestrator.

Runtime may be offline (n8n not running, etc.) — wrapper surfaces the
subprocess result including nonzero returncode rather than raising.
The caller decides how to react.

Resolves the dispatch_rbitr intent from runtime-dispatch.yaml and shells
out to the Rbitr HTTP orchestrator on :8765.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import dispatch_tool_result, run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-rbitr")

    @server.tool()
    def dispatch_to_rbitr(text: str) -> dict[str, Any]:
        """Dispatch a one-shot task to the Rbitr orchestrator HTTP API on :8765."""
        return dispatch_tool_result(run_intent("dispatch_rbitr", text=text))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
