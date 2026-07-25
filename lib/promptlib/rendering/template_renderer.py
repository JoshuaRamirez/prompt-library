"""`{{variable}}` substitution over a prompt body.

Chosen over str.format because prompt bodies routinely contain braces (JSON
examples, code) that format() would misparse. The double-brace form is rare in
prose and matches the convention already used across this user's prompt corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from ..errors import RenderError

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


@dataclass(frozen=True)
class RenderResult:
    """Outcome of a substitution pass."""

    text: str
    substituted: tuple[str, ...]
    unfilled: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "substituted": list(self.substituted),
            "unfilled": list(self.unfilled),
        }


class TemplateRenderer:
    """Substitutes `{{name}}` placeholders from a value mapping."""

    def placeholders(self, template: str) -> tuple[str, ...]:
        """Return placeholder names in first-appearance order."""
        seen: list[str] = []
        for match in _PLACEHOLDER.finditer(template):
            name = match.group(1)
            if name not in seen:
                seen.append(name)
        return tuple(seen)

    def render(
        self,
        template: str,
        values: Mapping[str, object],
        strict: bool = False,
    ) -> RenderResult:
        """Fill placeholders; in strict mode a missing value is an error."""
        substituted: list[str] = []
        unfilled: list[str] = []

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name in values and values[name] is not None:
                if name not in substituted:
                    substituted.append(name)
                return str(values[name])
            if name not in unfilled:
                unfilled.append(name)
            return match.group(0)

        text = _PLACEHOLDER.sub(replace, template)
        if strict and unfilled:
            raise RenderError(f"missing values for: {', '.join(unfilled)}")
        return RenderResult(text=text, substituted=tuple(substituted), unfilled=tuple(unfilled))
