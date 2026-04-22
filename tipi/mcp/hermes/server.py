"""Hermes MCP wrapper — dispatch task to the local Hermes runtime.

Runtime may be offline (model exhaustion, etc.) — wrapper surfaces the
subprocess result including a nonzero returncode rather than raising.
The caller decides how to react.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tipi.mcp._dispatch import run_intent


def build_server() -> FastMCP:
    server = FastMCP("tipi-hermes")

    @server.tool()
    def dispatch_to_hermes(text: str) -> dict[str, Any]:
        """Dispatch a one-shot task to the Hermes runtime.

        Wraps `hermes chat -Q -q "<text>"`. Returns the subprocess outcome.
        """
        result = run_intent("dispatch_hermes", text=text)
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
