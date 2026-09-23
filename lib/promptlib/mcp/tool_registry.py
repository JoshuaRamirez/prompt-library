"""The tool catalogue exposed over MCP.

Each entry is a thin projection of one `PromptLibraryService` method. Schemas are
written permissively — `additionalProperties: true` on write tools — because the
CSV is an open table: a caller may attach a column the library has never seen and
it must survive rather than be rejected at the boundary.
"""

from __future__ import annotations

from typing import Any

from ..errors import InvalidArgumentError
from ..service import PromptLibraryService
from .tool_definition import ToolDefinition

_STRING = {"type": "string"}
_STRING_LIST = {"type": "array", "items": {"type": "string"}}
_ID = {**_STRING, "description": "The prompt's id, e.g. 'code-review-checklist'."}
_LIMIT = {"type": "integer", "minimum": 1, "description": "Return at most this many."}
_INCLUDE_BODY = {"type": "boolean", "default": False, "description": "Include each prompt's full text."}


def _record_properties() -> dict[str, Any]:
    """The declared columns a caller may set. Any other property becomes a new column."""
    return {
        "title": {**_STRING, "description": "Short human-readable name."},
        "prompt": {**_STRING, "description": "The prompt text. {{name}} marks a placeholder."},
        "tags": {**_STRING_LIST, "description": "Keywords for finding it; a comma-separated string also works."},
        "category": {**_STRING, "description": "One grouping, e.g. 'engineering'."},
        "model": {**_STRING, "description": "The model the prompt is written for, if any."},
        "notes": {**_STRING, "description": "When and how to use it."},
        "source": {**_STRING, "description": "Where the prompt came from."},
        "version": {**_STRING, "description": "The user's own version label for the prompt."},
    }


def _facets() -> dict[str, Any]:
    return {
        "tags": {**_STRING_LIST, "description": "Only prompts carrying all of these tags."},
        "category": {**_STRING, "description": "Only prompts in this category."},
        "model": {**_STRING, "description": "Only prompts targeting this model."},
    }


def _flag(args: dict[str, Any], name: str) -> bool:
    """A boolean argument; the strings 'true' and 'false' are accepted, nothing else."""
    value = args.get(name, False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    raise InvalidArgumentError(f"{name} must be true or false, got {value!r}")


def _tags(args: dict[str, Any]) -> list[str] | None:
    """A tag list; a comma-separated string is split rather than read letter by letter."""
    value = args.get("tags")
    if value is None:
        return None
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return value
    raise InvalidArgumentError(f"tags must be a list of strings, got {value!r}")


def _values(args: dict[str, Any]) -> dict[str, Any]:
    value = args.get("values")
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InvalidArgumentError(
            "values must be an object mapping placeholder names to text, e.g. {\"language\": \"Go\"}"
        )
    return value


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
                        "query": {**_STRING, "description": "Words to look for."},
                        "limit": {**_LIMIT, "default": 10},
                        "include_body": _INCLUDE_BODY,
                        **_facets(),
                    },
                    "required": ["query"],
                },
                handler=lambda args: service.search(
                    query=str(args.get("query", "")),
                    limit=args.get("limit", 10),
                    tags=_tags(args),
                    category=args.get("category"),
                    model=args.get("model"),
                    include_body=_flag(args, "include_body"),
                ),
            ),
            ToolDefinition(
                name="prompt_list",
                description=(
                    "List prompts in file order, optionally filtered by tag, category or "
                    "model. Returns summaries without the prompt text unless include_body "
                    "is set."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": _LIMIT,
                        "include_body": _INCLUDE_BODY,
                        **_facets(),
                    },
                },
                handler=lambda args: {
                    "prompts": service.list(
                        tags=_tags(args),
                        category=args.get("category"),
                        model=args.get("model"),
                        limit=args.get("limit"),
                        include_body=_flag(args, "include_body"),
                    )
                },
            ),
            ToolDefinition(
                name="prompt_get",
                description="Fetch one prompt by id, including its full body and all columns.",
                input_schema={
                    "type": "object",
                    "properties": {"id": _ID},
                    "required": ["id"],
                },
                handler=lambda args: service.get(str(args.get("id", ""))),
            ),
            ToolDefinition(
                name="prompt_add",
                description=(
                    "Store a new prompt. Only 'prompt' is required. Without an id, one is "
                    "made from the title, or from the text when there is no title. "
                    "{{placeholders}} in the text are recorded as its variables. Any other "
                    "property becomes a new column in the CSV and is kept; the result's "
                    "new_columns lists any it created."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": {**_STRING, "description": "Explicit id; made from the title if omitted."},
                        **_record_properties(),
                    },
                    "required": ["prompt"],
                    "additionalProperties": True,
                },
                handler=lambda args: service.add(
                    {key: (_tags(args) if key == "tags" else value) for key, value in args.items() if key != "id"},
                    prompt_id=args.get("id"),
                ),
            ),
            ToolDefinition(
                name="prompt_update",
                description=(
                    "Change fields of a stored prompt. Supplied fields replace their values; "
                    "omitted fields are untouched. A new prompt text re-reads its variables. "
                    "Any other property becomes a new column; the result's new_columns lists "
                    "any it created, which is how a misspelt field shows up."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": _ID,
                        **_record_properties(),
                    },
                    "required": ["id"],
                    "additionalProperties": True,
                },
                handler=lambda args: service.update(
                    str(args.get("id", "")),
                    {key: (_tags(args) if key == "tags" else value) for key, value in args.items() if key != "id"},
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
                    "properties": {"id": _ID},
                    "required": ["id"],
                },
                handler=lambda args: service.delete(str(args.get("id", ""))),
            ),
            ToolDefinition(
                name="prompt_render",
                description=(
                    "Return a prompt's text with its {{placeholders}} filled from values. "
                    "Reports placeholders left unfilled, and values no placeholder used "
                    "(often a misspelt name)."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "id": _ID,
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
                    _values(args),
                    strict=_flag(args, "strict"),
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
