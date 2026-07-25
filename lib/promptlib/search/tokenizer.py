"""Lexical normalisation shared by indexing and querying.

Kept as its own unit so a future embedding backend can reuse the same text
preparation, or deliberately bypass it, without either decision leaking into the
strategy implementations.
"""

from __future__ import annotations

import re
from typing import Iterable

_WORD = re.compile(r"[a-z0-9_]+")

#: Terms carrying no discriminating power in a prompt corpus.
STOP_WORDS: frozenset[str] = frozenset(
    """
    a an the and or of to in for on with is are be as by that this it you your
    """.split()
)


class Tokenizer:
    """Lowercase word-boundary tokenizer with stop-word removal."""

    def __init__(self, stop_words: Iterable[str] = STOP_WORDS, min_length: int = 2) -> None:
        self._stop_words = frozenset(stop_words)
        self._min_length = min_length

    def tokenize(self, text: str) -> list[str]:
        """Split text into significant lowercase tokens."""
        return [
            token
            for token in _WORD.findall(text.lower())
            if len(token) >= self._min_length and token not in self._stop_words
        ]

    def tokenize_query(self, text: str) -> list[str]:
        """Tokenize a query, falling back to raw words if all terms were filtered."""
        tokens = self.tokenize(text)
        if tokens:
            return tokens
        return [token for token in _WORD.findall(text.lower()) if token]
