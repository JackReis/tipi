"""Ringside MCP wrapper — dispatch task to the Ringside HUD visibility surface.

Ringside is the read-only visibility projection layer per ADR-0019. This
wrapper resolves the dispatch_ringside intent from runtime-dispatch.yaml
and shells out to the Ringside HUD server (:8700) for visibility
projection requests.

Auth: ARBITER_ADMIN_TOKEN (shared with rbitr/arbiter — Ringside projection
requests are authorized by the same bearer token).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import dispatch_tool_result, run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-ringside")

    @server.tool()
    def dispatch_to_ringside(text: str) -> dict[str, Any]:
        """Dispatch a visibility projection request to the Ringside HUD on :8700.

        Accepts either a canonical intent name or a @-shortname alias (e.g.
        "@ringside") — aliases are resolved by the dispatch engine before
        command resolution.
        """
        return dispatch_tool_result(run_intent("@ringside", text=text))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
