"""Exact-match facet predicate over prompts.

Distinct from search: filtering is a boolean membership question answered from
declared columns, whereas search is a ranking question. Keeping them apart means
a future vector backend changes ranking without touching filtering, and filters
remain available as pre- or post-conditions on a semantic query.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .prompt import Prompt


@dataclass(frozen=True)
class PromptFilter:
    """Conjunction of facet constraints; empty fields impose no constraint."""

    tags: tuple[str, ...] = ()
    category: str = ""
    model: str = ""
    ids: tuple[str, ...] = ()

    @classmethod
    def build(
        cls,
        tags: Iterable[str] | None = None,
        category: str | None = None,
        model: str | None = None,
        ids: Iterable[str] | None = None,
    ) -> "PromptFilter":
        return cls(
            tags=tuple(tag.strip().lower() for tag in (tags or ()) if tag.strip()),
            category=(category or "").strip().lower(),
            model=(model or "").strip().lower(),
            ids=tuple(str(value).strip() for value in (ids or ()) if str(value).strip()),
        )

    @property
    def is_empty(self) -> bool:
        return not (self.tags or self.category or self.model or self.ids)

    def matches(self, prompt: Prompt) -> bool:
        """True when the prompt satisfies every constraint present."""
        if self.ids and prompt.id not in self.ids:
            return False
        if self.category and prompt.category.strip().lower() != self.category:
            return False
        if self.model and prompt.model.strip().lower() != self.model:
            return False
        if self.tags:
            owned = {tag.strip().lower() for tag in prompt.tags}
            if not set(self.tags).issubset(owned):
                return False
        return True

    def apply(self, prompts: Sequence[Prompt]) -> list[Prompt]:
        if self.is_empty:
            return list(prompts)
        return [prompt for prompt in prompts if self.matches(prompt)]
