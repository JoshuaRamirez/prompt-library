"""The tool catalogue exposed over MCP.

Each entry is a thin projection of one `PromptLibraryService` method. Schemas are
written permissively — `additionalProperties: true` on write tools — because the
CSV is an open table: a caller may attach a column the library has never seen and
it must survive rather than be rejected at the boundary.
"""

from __future__ import annotations

from typing import Any

from ..service import PromptLibraryService
from .tool_definition import ToolDefinition

_STRING = {"type": "string"}
_STRING_LIST = {"type": "array", "items": {"type": "string"}}


def _facets() -> dict[str, Any]:
    return {
        "tags": {**_STRING_LIST, "description": "Only prompts carrying all of these tags."},
        "category": {**_STRING, "description": "Only prompts in this category."},
        "model": {**_STRING, "description": "Only prompts targeting this model."},
    }


class ToolRegistry:
    """Builds and resolves the MCP tool set for a service instance."""

    def __init__(self, service: PromptLibraryService) -> None:
        self._service = service
        self._tools = {tool.name: tool for tool in self._build()}

    def list(self) -> list[dict[str, Any]]:
        return [tool.describe() for tool in self._tools.values()]

    def resolve(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    # -- catalogue -------------------------------------------------------

    def _build(self) -> list[ToolDefinition]:
        service = self._service
        return [
            ToolDefinition(
                name="prompt_search",
                description=(
                    "Search the prompt library by keyword and return ranked matches. "
                    "Use this first when looking for a stored prompt; it scores title, "
                    "tags, category, body, and notes. Facet arguments narrow the corpus "
                    "before ranking."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {**_STRING, "description": "Free-text query."},
                        "limit": {"type": "integer", "minimum": 1, "default": 10},
                        "include_body": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include full prompt text in each result.",
                        },
                        **_facets(),
                    },
                    "required": ["query"],
                },
                handler=lambda args: service.search(
                    query=str(args.get("query", "")),
                    limit=int(args.get("limit", 10)),
                    tags=args.get("tags"),
                    category=args.get("category"),
                    model=args.get("model"),
                    include_body=bool(args.get("include_body", False)),
                ),
            ),
            ToolDefinition(
                name="prompt_list",
                description=(
                    "List prompts in the library, newest columns included, optionally "
                    "filtered by tag, category, or model. Returns summaries without the "
                    "prompt body unless include_body is set."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1},
                        "include_body": {"type": "boolean", "default": False},
                        **_facets(),
                    },
                },
                handler=lambda args: {
                    "prompts": service.list(
                        tags=args.get("tags"),
                        category=args.get("category"),
                        model=args.get("model"),
                        limit=args.get("limit"),
                        include_body=bool(args.get("include_body", False)),
                    )
                },
            ),
            ToolDefinition(
                name="prompt_get",
                description="Fetch one prompt by id, including its full body and all columns.",
                input_schema={
                    "type": "object",
                    "properties": {"id": {**_STRING, "description": "Prompt id (slug)."}},
                    "required": ["id"],
                },
                handler=lambda args: service.get(str(args.get("id", ""))),
            ),
            ToolDefinition(
                name="prompt_add",
                description=(
                    "Store a new prompt. Only 'prompt' is required; an id is derived from "
                    "the title when omitted. Any property not in the declared schema becomes "
                    "a new column in the CSV and is preserved."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": {**_STRING, "description": "Explicit id; derived from title if omitted."},
                        "title": _STRING,
                        "prompt": {**_STRING, "description": "The prompt text itself."},
                        "tags": _STRING_LIST,
                        "category": _STRING,
                        "model": {**_STRING, "description": "Model this prompt is tuned for."},
                        "notes": _STRING,
                        "source": {**_STRING, "description": "Where the prompt came from."},
                        "version": _STRING,
                    },
                    "required": ["prompt"],
                    "additionalProperties": True,
                },
                handler=lambda args: service.add(
                    {key: value for key, value in args.items() if key != "id"},
                    prompt_id=args.get("id"),
                ),
            ),
            ToolDefinition(
                name="prompt_update",
                description=(
                    "Apply a partial update to a stored prompt. Supplied fields replace "
                    "existing values; omitted fields are untouched. Unknown fields become "
                    "new columns."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": _STRING,
                        "title": _STRING,
                        "prompt": _STRING,
                        "tags": _STRING_LIST,
                        "category": _STRING,
                        "model": _STRING,
                        "notes": _STRING,
                        "source": _STRING,
                        "version": _STRING,
                    },
                    "required": ["id"],
                    "additionalProperties": True,
                },
                handler=lambda args: service.update(
                    str(args.get("id", "")),
                    {key: value for key, value in args.items() if key != "id"},
                ),
            ),
            ToolDefinition(
                name="prompt_delete",
                description=(
                    "Delete a prompt by id and return the removed record. Irreversible; "
                    "confirm with the user before calling."
                ),
                input_schema={
                    "type": "object",
                    "properties": {"id": _STRING},
                    "required": ["id"],
                },
                handler=lambda args: service.delete(str(args.get("id", ""))),
            ),
            ToolDefinition(
                name="prompt_render",
                description=(
                    "Return a prompt body with its {{placeholders}} substituted from the "
                    "supplied values. Reports which placeholders remain unfilled."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": _STRING,
                        "values": {
                            "type": "object",
                            "description": "Placeholder name to replacement value.",
                            "additionalProperties": True,
                        },
                        "strict": {
                            "type": "boolean",
                            "default": False,
                            "description": "Fail instead of leaving placeholders unfilled.",
                        },
                    },
                    "required": ["id"],
                },
                handler=lambda args: service.render(
                    str(args.get("id", "")),
                    args.get("values") or {},
                    strict=bool(args.get("strict", False)),
                ),
            ),
            ToolDefinition(
                name="prompt_stats",
                description=(
                    "Report library size, CSV location, column set (including user-added "
                    "columns), and tag/category distributions."
                ),
                input_schema={"type": "object", "properties": {}},
                handler=lambda _args: service.stats(),
            ),
        ]
