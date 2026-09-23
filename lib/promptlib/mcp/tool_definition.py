"""A single MCP tool: its advertised contract plus the callable behind it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..errors import InvalidArgumentError

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
        """Check the schema's required arguments are present and non-blank, then call."""
        for name in self.input_schema.get("required", ()):
            value = arguments.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise InvalidArgumentError(f"missing required argument: {name}")
        return self.handler(arguments)
