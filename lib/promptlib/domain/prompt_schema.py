"""Canonical column set of the single `prompts` table.

Declared columns are the library's own vocabulary. Everything else a user adds
to the CSV is a *discovered* column: carried through reads and writes untouched
and exposed to callers as `extras`. That openness is why the store is a table
rather than a fixed record type — new facets cost a column, not a migration.
"""

from __future__ import annotations

from typing import Final

ID: Final = "id"
TITLE: Final = "title"
PROMPT: Final = "prompt"
TAGS: Final = "tags"
CATEGORY: Final = "category"
MODEL: Final = "model"
VARIABLES: Final = "variables"
NOTES: Final = "notes"
SOURCE: Final = "source"
VERSION: Final = "version"
CREATED_AT: Final = "created_at"
UPDATED_AT: Final = "updated_at"

DECLARED_COLUMNS: Final[tuple[str, ...]] = (
    ID,
    TITLE,
    PROMPT,
    TAGS,
    CATEGORY,
    MODEL,
    VARIABLES,
    NOTES,
    SOURCE,
    VERSION,
    CREATED_AT,
    UPDATED_AT,
)

#: Columns the library maintains; callers may not set them directly.
MANAGED_COLUMNS: Final[frozenset[str]] = frozenset({ID, CREATED_AT, UPDATED_AT})

#: Columns holding a comma-separated list rather than a scalar.
LIST_COLUMNS: Final[frozenset[str]] = frozenset({TAGS, VARIABLES})

#: Columns consulted by keyword search, with their relative weights.
SEARCHABLE_WEIGHTS: Final[dict[str, float]] = {
    TITLE: 3.0,
    TAGS: 2.5,
    CATEGORY: 2.0,
    PROMPT: 1.0,
    NOTES: 0.5,
}
