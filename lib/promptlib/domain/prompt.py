"""The Prompt record.

A Prompt is a thin, immutable projection over one CSV row. It owns conversion
between the flat string world of the table and the typed world callers expect
(lists for tags/variables, dict for user-added columns), and nothing else — no
persistence, no search, no rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from ..errors import InvalidPromptError
from . import prompt_schema as schema


def _split_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _join_list(values: Any) -> str:
    if isinstance(values, str):
        return ", ".join(_split_list(values))
    if values is None:
        return ""
    return ", ".join(str(item).strip() for item in values if str(item).strip())


@dataclass(frozen=True)
class Prompt:
    """One row of the prompts table."""

    id: str
    title: str = ""
    prompt: str = ""
    tags: tuple[str, ...] = ()
    category: str = ""
    model: str = ""
    variables: tuple[str, ...] = ()
    notes: str = ""
    source: str = ""
    version: str = ""
    created_at: str = ""
    updated_at: str = ""
    extras: Mapping[str, str] = field(default_factory=dict)

    # -- construction ----------------------------------------------------

    @classmethod
    def from_row(cls, row: Mapping[str, str]) -> "Prompt":
        """Build a Prompt from a raw CSV row, routing unknown keys to `extras`."""
        extras = {
            key: str(value or "")
            for key, value in row.items()
            if key not in schema.DECLARED_COLUMNS and key
        }
        return cls(
            id=str(row.get(schema.ID, "") or ""),
            title=str(row.get(schema.TITLE, "") or ""),
            prompt=str(row.get(schema.PROMPT, "") or ""),
            tags=tuple(_split_list(str(row.get(schema.TAGS, "") or ""))),
            category=str(row.get(schema.CATEGORY, "") or ""),
            model=str(row.get(schema.MODEL, "") or ""),
            variables=tuple(_split_list(str(row.get(schema.VARIABLES, "") or ""))),
            notes=str(row.get(schema.NOTES, "") or ""),
            source=str(row.get(schema.SOURCE, "") or ""),
            version=str(row.get(schema.VERSION, "") or ""),
            created_at=str(row.get(schema.CREATED_AT, "") or ""),
            updated_at=str(row.get(schema.UPDATED_AT, "") or ""),
            extras=extras,
        )

    @classmethod
    def from_fields(cls, fields: Mapping[str, Any]) -> "Prompt":
        """Build a Prompt from caller-supplied values of mixed type."""
        normalized = {
            key: (_join_list(value) if key in schema.LIST_COLUMNS else value)
            for key, value in fields.items()
        }
        return cls.from_row({key: "" if value is None else str(value) for key, value in normalized.items()})

    # -- projection ------------------------------------------------------

    def to_row(self) -> dict[str, str]:
        """Flatten back to a CSV row, extras included."""
        row: dict[str, str] = {
            schema.ID: self.id,
            schema.TITLE: self.title,
            schema.PROMPT: self.prompt,
            schema.TAGS: ", ".join(self.tags),
            schema.CATEGORY: self.category,
            schema.MODEL: self.model,
            schema.VARIABLES: ", ".join(self.variables),
            schema.NOTES: self.notes,
            schema.SOURCE: self.source,
            schema.VERSION: self.version,
            schema.CREATED_AT: self.created_at,
            schema.UPDATED_AT: self.updated_at,
        }
        row.update(self.extras)
        return row

    def to_dict(self) -> dict[str, Any]:
        """Typed projection for interface adapters (JSON, table rendering)."""
        payload: dict[str, Any] = {
            schema.ID: self.id,
            schema.TITLE: self.title,
            schema.PROMPT: self.prompt,
            schema.TAGS: list(self.tags),
            schema.CATEGORY: self.category,
            schema.MODEL: self.model,
            schema.VARIABLES: list(self.variables),
            schema.NOTES: self.notes,
            schema.SOURCE: self.source,
            schema.VERSION: self.version,
            schema.CREATED_AT: self.created_at,
            schema.UPDATED_AT: self.updated_at,
        }
        if self.extras:
            payload["extras"] = dict(self.extras)
        return payload

    def summary(self) -> dict[str, Any]:
        """Listing projection: identity and facets without the prompt body."""
        return {
            schema.ID: self.id,
            schema.TITLE: self.title,
            schema.TAGS: list(self.tags),
            schema.CATEGORY: self.category,
            schema.MODEL: self.model,
            "prompt_chars": len(self.prompt),
            schema.UPDATED_AT: self.updated_at,
        }

    # -- mutation (returns new instances) --------------------------------

    def merged_with(self, changes: Mapping[str, Any]) -> "Prompt":
        """Return a copy with `changes` applied; unknown keys land in `extras`."""
        declared: dict[str, Any] = {}
        extras = dict(self.extras)
        for key, value in changes.items():
            if key in schema.MANAGED_COLUMNS:
                continue
            if key in schema.LIST_COLUMNS:
                declared[key] = tuple(_split_list(_join_list(value)))
            elif key in schema.DECLARED_COLUMNS:
                declared[key] = "" if value is None else str(value)
            elif key:
                extras[key] = "" if value is None else str(value)
        return replace(self, extras=extras, **declared)

    def stamped(self, created_at: str | None = None, updated_at: str | None = None) -> "Prompt":
        """Return a copy carrying the given lifecycle timestamps."""
        return replace(
            self,
            created_at=created_at if created_at is not None else self.created_at,
            updated_at=updated_at if updated_at is not None else self.updated_at,
        )

    def with_id(self, prompt_id: str) -> "Prompt":
        return replace(self, id=prompt_id)

    # -- validation ------------------------------------------------------

    def validate(self) -> None:
        """Raise InvalidPromptError if the record is not fit to persist."""
        if not self.id.strip():
            raise InvalidPromptError("prompt id must not be empty")
        if not self.prompt.strip():
            raise InvalidPromptError(f"prompt {self.id!r} has an empty body")
