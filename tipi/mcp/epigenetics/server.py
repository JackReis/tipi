"""Epigenetics MCP wrapper — proxies nate-promptkit as a modulating input.

Promptkit sits alongside body/mind/spirit as an external expression-pattern
library. This wrapper re-exposes the read tools under the `tipi-epigenetics/*`
namespace so the agent plugin has stable local names.

Implementation note: the nate-promptkit MCP server is externally managed
(configured in Claude Code settings.json). This wrapper does NOT proxy the
network calls — it re-exports shape-matching tools that the host agent
framework can route to the real server via name alias, or for the agent
framework itself to import and call directly. For dispatchers that DO need
to shell out (e.g. CLI smoke tests), the `_source` helper below returns the
canonical tool name on the upstream server.

This is the minimum viable shape. A future session can promote this to a
true proxy (HTTP bridge) if a stable nate-promptkit HTTP surface emerges.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP


# Upstream tool names (mcp__nate-promptkit__*) that this wrapper re-exports
# under the tipi-epigenetics namespace. Kept as a stable map so agent
# definitions can reference `tipi-epigenetics/search_prompt_kits` regardless
# of whether the upstream tool is renamed.
UPSTREAM = {
    "search_prompt_kits": "mcp__nate-promptkit__search_prompt_kits",
    "get_prompt_kit": "mcp__nate-promptkit__get_prompt_kit",
    "list_prompt_kits": "mcp__nate-promptkit__list_prompt_kits",
    "search_guides": "mcp__nate-promptkit__search_guides",
    "search_posts": "mcp__nate-promptkit__search_posts",
}


def _source(local_name: str) -> str:
    """Return the upstream nate-promptkit tool name for a given local name."""
    try:
        return UPSTREAM[local_name]
    except KeyError as exc:
        known = ", ".join(sorted(UPSTREAM))
        raise KeyError(f"unknown epigenetics tool {local_name!r}; known: {known}") from exc


def build_server() -> FastMCP:
    server = FastMCP("tipi-epigenetics")

    @server.tool()
    def upstream_for(local_name: str) -> dict[str, Any]:
        """Return the upstream nate-promptkit tool that local_name maps to.

        Agents call this to discover which real MCP tool to invoke. This
        keeps the epigenetics contract stable (tipi-epigenetics/*) while
        allowing the upstream surface to evolve.
        """
        return {"local": local_name, "upstream": _source(local_name)}

    @server.tool()
    def list_epigenetic_sources() -> list[dict[str, str]]:
        """Enumerate the upstream tools this wrapper bridges to."""
        return [{"local": k, "upstream": v} for k, v in sorted(UPSTREAM.items())]

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
