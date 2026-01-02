"""Minimal MCP server skeleton to expose local tools securely.

This should run in the local environment and surface safe tool endpoints to cloud agents.
"""

from typing import Callable, Dict


class MCPServer:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable) -> None:
        # Register a callable tool; ensure it is privacy-safe before exposing.
        self.tools[name] = func

    def invoke(self, name: str, *args, **kwargs):
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found")
        return self.tools[name](*args, **kwargs)


def build_server() -> MCPServer:
    server = MCPServer()
    # TODO: register gatekeeper-safe tools here (e.g., pseudonymize, depseudonymize).
    return server
