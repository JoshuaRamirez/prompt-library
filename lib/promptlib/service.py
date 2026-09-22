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
        corpus = PromptFilter.build(tags=tags, category=category, model=model).apply(
            self._repository.list()
        )
        self._strategy.index(corpus)
        hits = self._strategy.search(query, corpus, limit=limit)
        return {
            "query": query,
            "strategy": self._strategy.name,
            "candidates": len(corpus),
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
        tag_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        for prompt in prompts:
            for tag in prompt.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if prompt.category:
                category_counts[prompt.category] = category_counts.get(prompt.category, 0) + 1
        return {
            "csv_path": str(self._repository_table_path()),
            "count": len(prompts),
            "columns": list(self._repository.columns()),
            "extra_columns": [
                column
                for column in self._repository.columns()
                if column not in schema.DECLARED_COLUMNS
            ],
            "tags": dict(sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))),
            "categories": dict(
                sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
            ),
            "total_prompt_chars": sum(len(prompt.prompt) for prompt in prompts),
            "search_strategy": self._strategy.name,
        }

    # -- writes ----------------------------------------------------------

    def add(self, fields: Mapping[str, Any], prompt_id: str | None = None) -> dict[str, Any]:
        """Insert a prompt. Unknown keys become new CSV columns."""
        prepared = dict(fields)
        prepared.setdefault(schema.VARIABLES, list(self._renderer.placeholders(str(prepared.get(schema.PROMPT, "")))))
        return self._repository.add(prepared, prompt_id=prompt_id).to_dict()

    def update(self, prompt_id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        """Apply a partial update; unknown keys become new CSV columns."""
        prepared = dict(changes)
        if schema.PROMPT in prepared and schema.VARIABLES not in prepared:
            prepared[schema.VARIABLES] = list(
                self._renderer.placeholders(str(prepared[schema.PROMPT]))
            )
        return self._repository.update(prompt_id, prepared).to_dict()

    def delete(self, prompt_id: str) -> dict[str, Any]:
        """Remove a prompt and return the removed record."""
        return self._repository.delete(prompt_id).to_dict()

    def import_rows(self, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Insert or replace a batch of records matched by id."""
        written = self._repository.upsert_many(rows)
        return {"written": len(written), "ids": [prompt.id for prompt in written]}

    # -- internals -------------------------------------------------------

    def _repository_table_path(self) -> Path:
        if self._paths is not None:
            return self._paths.csv_path
        return LibraryPaths.resolve().csv_path


__all__ = ["PromptLibraryService", "Prompt"]
