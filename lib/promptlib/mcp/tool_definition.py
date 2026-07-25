"""A single MCP tool: its advertised contract plus the callable behind it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

Handler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolDefinition:
    """Binds an MCP tool name and JSON Schema to a service call."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Handler

    def describe(self) -> dict[str, Any]:
        """The tools/list projection."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def invoke(self, arguments: dict[str, Any]) -> Any:
        return self.handler(arguments)
