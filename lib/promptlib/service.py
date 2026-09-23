"""Facade over repository, filter, search strategy, and renderer.

This is the single surface both interface adapters (CLI, MCP) consume, so the
two never drift in behaviour and neither reaches past it into the layers below.
Returned values are plain JSON-compatible structures — adapters format, they do
not compute.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .clock import Clock
from .config import LibraryPaths
from .domain import prompt_schema as schema
from .domain.prompt import Prompt
from .domain.prompt_filter import PromptFilter
from .domain.prompt_repository import PromptRepository
from .errors import InvalidArgumentError
from .rendering.template_renderer import TemplateRenderer
from .search.keyword_strategy import KeywordSearchStrategy
from .search.search_strategy import SearchStrategy
from .storage.csv_table import CsvTable


class PromptLibraryService:
    """Application-level operations on the prompt library."""

    def __init__(
        self,
        repository: PromptRepository,
        strategy: SearchStrategy | None = None,
        renderer: TemplateRenderer | None = None,
        paths: LibraryPaths | None = None,
    ) -> None:
        self._repository = repository
        self._strategy = strategy or KeywordSearchStrategy()
        self._renderer = renderer or TemplateRenderer()
        self._paths = paths

    # -- construction ----------------------------------------------------

    @classmethod
    def open(
        cls,
        csv_path: str | Path | None = None,
        strategy: SearchStrategy | None = None,
        clock: Clock | None = None,
    ) -> "PromptLibraryService":
        """Build a service bound to the resolved CSV location."""
        paths = LibraryPaths.resolve(csv_path)
        table = CsvTable(paths.csv_path, schema.ID, schema.DECLARED_COLUMNS)
        repository = PromptRepository(table, clock=clock)
        repository.initialize()
        return cls(repository, strategy=strategy, paths=paths)

    @property
    def csv_path(self) -> Path:
        return self._repository_table_path()

    # -- reads -----------------------------------------------------------

    def list(
        self,
        tags: Iterable[str] | None = None,
        category: str | None = None,
        model: str | None = None,
        limit: int | None = None,
        include_body: bool = False,
    ) -> list[dict[str, Any]]:
        """List prompts, optionally narrowed by facets."""
        _check_limit(limit)
        prompts = PromptFilter.build(tags=tags, category=category, model=model).apply(
            self._repository.list()
        )
        if limit is not None:
            prompts = prompts[:limit]
        return [prompt.to_dict() if include_body else prompt.summary() for prompt in prompts]

    def get(self, prompt_id: str) -> dict[str, Any]:
        """Return the full record for one prompt."""
        return self._repository.get(prompt_id).to_dict()

    def search(
        self,
        query: str,
        limit: int = 10,
        tags: Iterable[str] | None = None,
        category: str | None = None,
        model: str | None = None,
        include_body: bool = False,
    ) -> dict[str, Any]:
        """Rank prompts against `query`, restricted to any facets supplied.

        Filtering runs before ranking so facets act as hard constraints, which is
        the behaviour a hybrid vector backend should preserve.
        """
        _check_limit(limit)
        corpus = PromptFilter.build(tags=tags, category=category, model=model).apply(
            self._repository.list()
        )
        self._strategy.index(corpus)
        # Rank everything, then cut, so `matched` reports all hits, not just the page.
        ranked = self._strategy.search(query, corpus, limit=max(len(corpus), 1))
        hits = ranked[:limit]
        return {
            "query": query,
            "strategy": self._strategy.name,
            "candidates": len(corpus),
            "matched": len(ranked),
            "count": len(hits),
            "results": [hit.to_dict(include_body=include_body) for hit in hits],
        }

    def render(
        self,
        prompt_id: str,
        values: Mapping[str, Any] | None = None,
        strict: bool = False,
    ) -> dict[str, Any]:
        """Return the prompt body with `{{variables}}` substituted."""
        prompt = self._repository.get(prompt_id)
        result = self._renderer.render(prompt.prompt, values or {}, strict=strict)
        payload = result.to_dict()
        payload["id"] = prompt.id
        payload["title"] = prompt.title
        payload["declared_variables"] = list(prompt.variables)
        return payload

    def stats(self) -> dict[str, Any]:
        """Summarise the library: counts, facets, and storage location."""
        prompts = self._repository.list()
        # Filters ignore case, so the counts do too; each is shown as first spelled.
        tag_counts = _CaseInsensitiveTally()
        category_counts = _CaseInsensitiveTally()
        for prompt in prompts:
            for tag in prompt.tags:
                tag_counts.add(tag)
            if prompt.category:
                category_counts.add(prompt.category)
        return {
            "csv_path": str(self._repository_table_path()),
            "count": len(prompts),
            "columns": list(self._repository.columns()),
            "extra_columns": [
                column
                for column in self._repository.columns()
                if column not in schema.DECLARED_COLUMNS
            ],
            "tags": tag_counts.ranked(),
            "categories": category_counts.ranked(),
            "total_prompt_chars": sum(len(prompt.prompt) for prompt in prompts),
            "search_strategy": self._strategy.name,
        }

    # -- writes ----------------------------------------------------------

    def add(self, fields: Mapping[str, Any], prompt_id: str | None = None) -> dict[str, Any]:
        """Insert a prompt. Unknown keys become new CSV columns."""
        prepared = _checked_fields(fields, managed=(schema.CREATED_AT, schema.UPDATED_AT))
        prepared.setdefault(schema.VARIABLES, list(self._renderer.placeholders(str(prepared.get(schema.PROMPT, "")))))
        return self._with_new_columns(lambda: self._repository.add(prepared, prompt_id=prompt_id))

    def update(self, prompt_id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        """Apply a partial update; unknown keys become new CSV columns."""
        prepared = _checked_fields(changes, managed=tuple(schema.MANAGED_COLUMNS))
        if not prepared:
            raise InvalidArgumentError("no changes supplied")
        self._derive_variables(prepared)
        return self._with_new_columns(lambda: self._repository.update(prompt_id, prepared))

    def delete(self, prompt_id: str) -> dict[str, Any]:
        """Remove a prompt and return the removed record."""
        return self._repository.delete(prompt_id).to_dict()

    def import_rows(self, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Add new records and update existing ones, matched by id.

        An existing prompt changes only in the fields a record supplies. The
        managed columns (id aside, which does the matching) are ignored, so the
        output of `list --full --json` imports back cleanly.
        """
        prepared = []
        for number, row in enumerate(rows, start=1):
            try:
                fields = _checked_fields(row, managed=())
            except InvalidArgumentError as exc:
                raise InvalidArgumentError(f"record {number}: {exc}") from exc
            self._derive_variables(fields)
            prepared.append(fields)
        written = self._repository.upsert_many(prepared)
        return {"written": len(written), "ids": [prompt.id for prompt in written]}

    # -- internals -------------------------------------------------------

    def _derive_variables(self, fields: dict[str, Any]) -> None:
        """A new body brings its own placeholder list unless one is supplied."""
        if schema.PROMPT in fields and schema.VARIABLES not in fields:
            fields[schema.VARIABLES] = list(self._renderer.placeholders(str(fields[schema.PROMPT] or "")))

    def _with_new_columns(self, write) -> dict[str, Any]:
        """Run a write and report any column it added, so a misspelt field is visible."""
        before = set(self._repository.columns())
        payload = write().to_dict()
        added = [column for column in self._repository.columns() if column not in before]
        if added:
            payload["new_columns"] = added
        return payload

    def _repository_table_path(self) -> Path:
        if self._paths is not None:
            return self._paths.csv_path
        return LibraryPaths.resolve().csv_path


def _check_limit(limit: Any) -> None:
    """A limit is absent or a positive integer; anything else is a caller error."""
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise InvalidArgumentError(f"limit must be a positive integer, got {limit!r}")


def _checked_fields(fields: Mapping[str, Any], managed: Sequence[str]) -> dict[str, Any]:
    """Copy caller fields, refusing managed columns and values a CSV cell cannot hold."""
    checked: dict[str, Any] = {}
    for key, value in fields.items():
        if key in managed:
            raise InvalidArgumentError(f"{key!r} is managed by the library and cannot be set")
        if isinstance(value, Mapping) or (
            isinstance(value, (list, tuple)) and key not in schema.LIST_COLUMNS
        ):
            raise InvalidArgumentError(f"{key!r} must be text, not {type(value).__name__}")
        checked[key] = value
    return checked


class _CaseInsensitiveTally:
    """Counts values ignoring case, remembering the first spelling of each."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._spelling: dict[str, str] = {}

    def add(self, value: str) -> None:
        key = value.casefold()
        self._spelling.setdefault(key, value)
        self._counts[key] = self._counts.get(key, 0) + 1

    def ranked(self) -> dict[str, int]:
        order = sorted(self._counts.items(), key=lambda item: (-item[1], item[0]))
        return {self._spelling[key]: count for key, count in order}


__all__ = ["PromptLibraryService", "Prompt"]
