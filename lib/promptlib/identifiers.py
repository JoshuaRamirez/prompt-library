"""Identifier derivation.

Ids are human-legible slugs so a CSV opened in a spreadsheet stays readable and
so prompts can be referenced conversationally ("use code-review-strict").
"""

from __future__ import annotations

import re
import unicodedata
from typing import Callable, Iterable

_NON_SLUG = re.compile(r"[^a-z0-9]+")
_TRIM = re.compile(r"^-+|-+$")


class SlugFactory:
    """Derives collision-free slug identifiers from free text."""

    def __init__(self, max_length: int = 60) -> None:
        self._max_length = max_length

    def slugify(self, text: str) -> str:
        """Reduce arbitrary text to a lowercase hyphenated ASCII slug."""
        folded = unicodedata.normalize("NFKD", text)
        ascii_only = folded.encode("ascii", "ignore").decode("ascii")
        slug = _NON_SLUG.sub("-", ascii_only.lower())
        slug = _TRIM.sub("", slug)[: self._max_length]
        slug = _TRIM.sub("", slug)
        return slug or "prompt"

    def unique(self, text: str, taken: Iterable[str]) -> str:
        """Return a slug for `text` not present in `taken`, suffixing -2, -3, ..."""
        existing = set(taken)
        base = self.slugify(text)
        if base not in existing:
            return base
        for suffix in range(2, 10_000):
            candidate = f"{base}-{suffix}"
            if candidate not in existing:
                return candidate
        raise ValueError(f"exhausted slug space for {base!r}")


IdSource = Callable[[str, Iterable[str]], str]
"""Signature of an id allocator: (seed_text, taken_ids) -> id."""
