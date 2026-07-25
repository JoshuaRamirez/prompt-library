"""A single CSV file addressed as an open-schema keyed table.

Deliberately ignorant of prompts: it knows a key column, an ordered column set,
and how to read/write the whole file under lock. Row values are strings; typing
and validation belong to the domain layer above.

Whole-file rewrite is the chosen strategy. A personal prompt library is on the
order of hundreds of rows, so the cost is irrelevant next to the guarantee that
the file on disk is always a complete, well-formed CSV.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence, TextIO

from ..errors import StoreCorruptionError
from .atomic_writer import AtomicFileWriter
from .file_lock import FileLock
from .table_schema import TableSchema

# Prompt bodies routinely exceed the default 128 KiB field limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


class CsvTable:
    """Read/write access to one CSV file keyed by a designated column."""

    def __init__(self, path: Path, key_column: str, declared_columns: Sequence[str]) -> None:
        self._path = path
        self._key_column = key_column
        self._declared = tuple(declared_columns)
        if key_column not in self._declared:
            raise ValueError(f"key column {key_column!r} must be among declared columns")

    @property
    def path(self) -> Path:
        return self._path

    @property
    def key_column(self) -> str:
        return self._key_column

    def exists(self) -> bool:
        return self._path.exists()

    def schema(self) -> TableSchema:
        """Return the on-disk column set, or the declared set if the file is absent."""
        header = self._read_header()
        return TableSchema(self._declared, header)

    def read_all(self) -> list[dict[str, str]]:
        """Return every row as a dict projected onto the current schema."""
        if not self._path.exists():
            return []
        schema = self.schema()
        try:
            with self._path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    return []
                return [schema.normalize(row) for row in reader]
        except (OSError, csv.Error) as exc:
            raise StoreCorruptionError(f"cannot read {self._path}: {exc}") from exc

    def write_all(self, rows: Iterable[Mapping[str, str]]) -> TableSchema:
        """Replace the file with `rows`, widening the schema to fit them."""
        materialized = [dict(row) for row in rows]
        schema = self.schema().widen_for(materialized)
        writer = AtomicFileWriter(self._path)
        writer.write(lambda handle: self._emit(handle, schema, materialized))
        return schema

    def lock(self) -> FileLock:
        """Acquire the advisory lock guarding read-modify-write cycles."""
        return FileLock(self._path)

    def initialize(self) -> TableSchema:
        """Create the file with a header row if it does not yet exist."""
        if self._path.exists():
            return self.schema()
        return self.write_all([])

    def _emit(
        self,
        handle: TextIO,
        schema: TableSchema,
        rows: Sequence[Mapping[str, str]],
    ) -> None:
        writer = csv.DictWriter(handle, fieldnames=list(schema.columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(schema.normalize(row))

    def _read_header(self) -> list[str]:
        if not self._path.exists():
            return []
        try:
            with self._path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                return next(reader, [])
        except (OSError, csv.Error) as exc:
            raise StoreCorruptionError(f"cannot read header of {self._path}: {exc}") from exc
