"""Collection-like access to the persisted prompts.

The repository owns identity allocation, lifecycle timestamps, and the
read-modify-write cycle. Every mutation runs inside the table's advisory lock
and re-reads from disk first, so concurrent sessions cannot clobber each other
with a stale in-memory copy.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from ..clock import Clock
from ..errors import DuplicatePromptError, PromptNotFoundError
from ..identifiers import SlugFactory
from ..storage.csv_table import CsvTable
from . import prompt_schema as schema
from .prompt import Prompt


class PromptRepository:
    """CRUD over the single prompts table."""

    def __init__(
        self,
        table: CsvTable,
        clock: Clock | None = None,
        slugs: SlugFactory | None = None,
    ) -> None:
        self._table = table
        self._clock = clock or Clock()
        self._slugs = slugs or SlugFactory()

    # -- reads -----------------------------------------------------------

    def list(self) -> list[Prompt]:
        """Return every prompt in file order."""
        return [Prompt.from_row(row) for row in self._table.read_all()]

    def get(self, prompt_id: str) -> Prompt:
        """Return one prompt or raise PromptNotFoundError."""
        for prompt in self.list():
            if prompt.id == prompt_id:
                return prompt
        raise PromptNotFoundError(prompt_id)

    def find(self, prompt_id: str) -> Prompt | None:
        """Return one prompt or None."""
        try:
            return self.get(prompt_id)
        except PromptNotFoundError:
            return None

    def ids(self) -> list[str]:
        return [prompt.id for prompt in self.list()]

    def columns(self) -> tuple[str, ...]:
        """Current on-disk column set, declared columns first."""
        return self._table.schema().columns

    # -- writes ----------------------------------------------------------

    def add(self, fields: Mapping[str, Any], prompt_id: str | None = None) -> Prompt:
        """Insert a new prompt, deriving an id from the title when absent."""
        with self._table.lock():
            existing = self.list()
            taken = {prompt.id for prompt in existing}
            candidate = Prompt.from_fields(fields)
            resolved_id = (prompt_id or candidate.id or "").strip()
            if resolved_id:
                if resolved_id in taken:
                    raise DuplicatePromptError(resolved_id)
            else:
                seed = candidate.title or candidate.prompt[:60]
                resolved_id = self._slugs.unique(seed, taken)
            now = self._clock.now_iso()
            record = candidate.with_id(resolved_id).stamped(created_at=now, updated_at=now)
            record.validate()
            self._table.write_all([row.to_row() for row in existing] + [record.to_row()])
            return record

    def update(self, prompt_id: str, changes: Mapping[str, Any]) -> Prompt:
        """Apply a partial update to an existing prompt."""
        with self._table.lock():
            existing = self.list()
            index = self._index_of(existing, prompt_id)
            updated = existing[index].merged_with(changes).stamped(updated_at=self._clock.now_iso())
            updated.validate()
            existing[index] = updated
            self._table.write_all([row.to_row() for row in existing])
            return updated

    def delete(self, prompt_id: str) -> Prompt:
        """Remove a prompt and return the record that was removed."""
        with self._table.lock():
            existing = self.list()
            index = self._index_of(existing, prompt_id)
            removed = existing.pop(index)
            self._table.write_all([row.to_row() for row in existing])
            return removed

    def upsert_many(self, records: Iterable[Mapping[str, Any]]) -> list[Prompt]:
        """Insert or replace a batch, matching on id. Used by import."""
        with self._table.lock():
            existing = self.list()
            by_id = {prompt.id: position for position, prompt in enumerate(existing)}
            now = self._clock.now_iso()
            written: list[Prompt] = []
            for fields in records:
                candidate = Prompt.from_fields(fields)
                target_id = candidate.id.strip() or self._slugs.unique(
                    candidate.title or candidate.prompt[:60], by_id.keys()
                )
                if target_id in by_id:
                    position = by_id[target_id]
                    merged = existing[position].merged_with(candidate.to_row()).stamped(updated_at=now)
                    merged.validate()
                    existing[position] = merged
                    written.append(merged)
                else:
                    record = candidate.with_id(target_id).stamped(created_at=now, updated_at=now)
                    record.validate()
                    by_id[target_id] = len(existing)
                    existing.append(record)
                    written.append(record)
            self._table.write_all([row.to_row() for row in existing])
            return written

    def initialize(self) -> None:
        """Ensure the backing file exists with a header row."""
        with self._table.lock():
            self._table.initialize()

    # -- internals -------------------------------------------------------

    @staticmethod
    def _index_of(prompts: Sequence[Prompt], prompt_id: str) -> int:
        for position, prompt in enumerate(prompts):
            if prompt.id == prompt_id:
                return position
        raise PromptNotFoundError(prompt_id)


__all__ = ["PromptRepository", "schema"]
