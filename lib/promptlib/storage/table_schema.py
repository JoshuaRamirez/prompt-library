"""Column-set management for an open-schema CSV table.

The table is *open*: a caller may attach columns the library has never seen, and
those columns survive read-modify-write cycles. `TableSchema` keeps declared
columns in a fixed leading order and appends discovered columns after them, so
the file stays predictable to a human reader while remaining extensible.
"""

from __future__ import annotations

from typing import Iterable, Iterator, Mapping, Sequence


class TableSchema:
    """An ordered column set: declared columns first, discovered columns after."""

    def __init__(self, declared: Sequence[str], discovered: Iterable[str] = ()) -> None:
        self._declared = tuple(declared)
        seen = set(self._declared)
        extra: list[str] = []
        for column in discovered:
            if column and column not in seen:
                seen.add(column)
                extra.append(column)
        self._discovered = tuple(extra)

    @property
    def declared(self) -> tuple[str, ...]:
        return self._declared

    @property
    def discovered(self) -> tuple[str, ...]:
        return self._discovered

    @property
    def columns(self) -> tuple[str, ...]:
        return self._declared + self._discovered

    def __iter__(self) -> Iterator[str]:
        return iter(self.columns)

    def __contains__(self, column: object) -> bool:
        return column in self.columns

    def extended_with(self, columns: Iterable[str]) -> "TableSchema":
        """Return a schema widened by any columns not already present."""
        return TableSchema(self._declared, list(self._discovered) + list(columns))

    def widen_for(self, rows: Iterable[Mapping[str, str]]) -> "TableSchema":
        """Return a schema wide enough to hold every key appearing in `rows`."""
        keys: list[str] = []
        for row in rows:
            keys.extend(row.keys())
        return self.extended_with(keys)

    def normalize(self, row: Mapping[str, str]) -> dict[str, str]:
        """Project a row onto this schema, filling absent columns with ''."""
        return {column: str(row.get(column, "") or "") for column in self.columns}
