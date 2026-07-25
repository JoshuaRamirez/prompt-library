"""The retrieval port.

Every retrieval mechanism — the lexical one shipped today, a dense-vector one
later, a hybrid reranker after that — satisfies this one interface. Callers
above (the service, and therefore the CLI and MCP tools) depend on the port, not
on any implementation, so swapping backends is a construction-time decision.

Contract:
  * `search` is a total function over the supplied corpus; it never mutates it.
  * Hits are returned in descending `score` order, ties broken deterministically.
  * `score` is comparable only within one strategy, not across strategies.
  * `index` is an optional optimisation hook; a strategy that needs no
    precomputation implements it as a no-op and remains correct.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Sequence

from ..domain.prompt import Prompt


@dataclass(frozen=True)
class SearchHit:
    """One scored retrieval result."""

    prompt: Prompt
    score: float
    matched_fields: tuple[str, ...] = ()
    explain: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_body: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = self.prompt.to_dict() if include_body else self.prompt.summary()
        payload["score"] = round(self.score, 4)
        payload["matched_fields"] = list(self.matched_fields)
        return payload


class SearchStrategy(ABC):
    """Port: rank prompts against a free-text query."""

    #: Stable identifier reported to callers so results are attributable.
    name: str = "abstract"

    def index(self, prompts: Sequence[Prompt]) -> None:  # noqa: B027 - intentional no-op default
        """Precompute whatever the strategy needs. Default: nothing."""
        return None

    @abstractmethod
    def search(self, query: str, prompts: Sequence[Prompt], limit: int = 10) -> list[SearchHit]:
        """Return up to `limit` hits ranked by descending relevance."""
        raise NotImplementedError
