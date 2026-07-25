"""Lexical retrieval over the prompts table.

Scoring is field-weighted term frequency with a phrase bonus — deliberately
simple and explainable, since at personal-library scale precision comes from the
weights, not from the ranking function. It is exact on identifiers and tags,
which is where a purely semantic backend is weakest; that complementarity is the
argument for keeping this strategy after a vector backend arrives rather than
replacing it.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from ..domain import prompt_schema as schema
from ..domain.prompt import Prompt
from .search_strategy import SearchHit, SearchStrategy
from .tokenizer import Tokenizer


class KeywordSearchStrategy(SearchStrategy):
    """Field-weighted lexical scoring with substring and phrase bonuses."""

    name = "keyword"

    def __init__(
        self,
        tokenizer: Tokenizer | None = None,
        weights: dict[str, float] | None = None,
        phrase_bonus: float = 2.0,
    ) -> None:
        self._tokenizer = tokenizer or Tokenizer()
        self._weights = dict(weights or schema.SEARCHABLE_WEIGHTS)
        self._phrase_bonus = phrase_bonus

    def search(self, query: str, prompts: Sequence[Prompt], limit: int = 10) -> list[SearchHit]:
        terms = self._tokenizer.tokenize_query(query)
        if not terms:
            return []
        phrase = query.strip().lower()
        hits: list[SearchHit] = []
        for prompt in prompts:
            hit = self._score(prompt, terms, phrase)
            if hit is not None:
                hits.append(hit)
        hits.sort(key=lambda hit: (-hit.score, hit.prompt.id))
        return hits[:limit]

    # -- internals -------------------------------------------------------

    def _score(self, prompt: Prompt, terms: Sequence[str], phrase: str) -> SearchHit | None:
        total = 0.0
        matched: list[str] = []
        per_field: dict[str, float] = {}
        for column, weight in self._weights.items():
            text = self._field_text(prompt, column)
            if not text:
                continue
            field_score = self._field_score(text, terms, phrase, weight)
            if field_score > 0:
                total += field_score
                matched.append(column)
                per_field[column] = round(field_score, 4)
        if total <= 0:
            return None
        return SearchHit(
            prompt=prompt,
            score=total,
            matched_fields=tuple(matched),
            explain={"strategy": self.name, "fields": per_field},
        )

    def _field_score(self, text: str, terms: Sequence[str], phrase: str, weight: float) -> float:
        counts = Counter(self._tokenizer.tokenize(text))
        lowered = text.lower()
        score = 0.0
        for term in terms:
            occurrences = counts.get(term, 0)
            if occurrences:
                # Sub-linear in frequency: presence matters more than repetition.
                score += weight * (1.0 + math.log(occurrences))
            elif term in lowered:
                # Partial/substring match (e.g. "review" inside "code-review").
                score += weight * 0.4
        if score > 0 and phrase and phrase in lowered:
            score += weight * self._phrase_bonus
        return score

    @staticmethod
    def _field_text(prompt: Prompt, column: str) -> str:
        if column == schema.TAGS:
            return " ".join(prompt.tags)
        if column == schema.VARIABLES:
            return " ".join(prompt.variables)
        value = getattr(prompt, column, "")
        return value if isinstance(value, str) else str(value)
