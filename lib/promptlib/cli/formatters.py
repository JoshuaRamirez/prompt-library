"""Terminal presentation of service payloads.

Presentation is isolated here so `--json` and the human view are two renderings
of one result, never two code paths producing two different truths.
"""

from __future__ import annotations

import json
import shutil
from typing import Any, Mapping, Sequence


class JsonFormatter:
    """Machine-readable rendering."""

    def render(self, payload: Any) -> str:
        return json.dumps(payload, indent=2, ensure_ascii=False)


class TextFormatter:
    """Human-readable rendering."""

    def __init__(self, width: int | None = None) -> None:
        self._width = width or min(shutil.get_terminal_size((100, 24)).columns, 120)

    # -- listings --------------------------------------------------------

    def summaries(self, rows: Sequence[Mapping[str, Any]]) -> str:
        if not rows:
            return "(no prompts)"
        lines = []
        id_width = max(len(str(row.get("id", ""))) for row in rows)
        for row in rows:
            tags = ", ".join(row.get("tags") or [])
            facets = " ".join(
                part
                for part in (
                    f"[{row['category']}]" if row.get("category") else "",
                    f"#{tags}" if tags else "",
                )
                if part
            )
            score = f" ({row['score']:.2f})" if "score" in row else ""
            title = str(row.get("title", "") or "")
            lines.append(f"{str(row.get('id','')):<{id_width}}  {title}{score}  {facets}".rstrip())
        return "\n".join(lines)

    def search(self, payload: Mapping[str, Any]) -> str:
        results = payload.get("results") or []
        header = (
            f"{payload.get('count', 0)} of {payload.get('candidates', 0)} prompts matched "
            f"'{payload.get('query', '')}' via {payload.get('strategy', '?')}"
        )
        return f"{header}\n{self.summaries(results)}"

    # -- records ---------------------------------------------------------

    def record(self, prompt: Mapping[str, Any]) -> str:
        lines = [f"id:         {prompt.get('id','')}"]
        for label, key in (
            ("title", "title"),
            ("category", "category"),
            ("model", "model"),
            ("version", "version"),
            ("source", "source"),
        ):
            value = prompt.get(key)
            if value:
                lines.append(f"{label + ':':<11} {value}")
        for label, key in (("tags", "tags"), ("variables", "variables")):
            values = prompt.get(key) or []
            if values:
                lines.append(f"{label + ':':<11} {', '.join(values)}")
        for label, key in (("created", "created_at"), ("updated", "updated_at")):
            if prompt.get(key):
                lines.append(f"{label + ':':<11} {prompt[key]}")
        for key, value in (prompt.get("extras") or {}).items():
            if value:
                lines.append(f"{key + ':':<11} {value}")
        if prompt.get("notes"):
            lines.append(f"{'notes:':<11} {prompt['notes']}")
        lines.append("-" * min(self._width, 72))
        lines.append(str(prompt.get("prompt", "")))
        return "\n".join(lines)

    def stats(self, payload: Mapping[str, Any]) -> str:
        lines = [
            f"csv:        {payload.get('csv_path','')}",
            f"prompts:    {payload.get('count', 0)}",
            f"strategy:   {payload.get('search_strategy','')}",
            f"columns:    {', '.join(payload.get('columns') or [])}",
        ]
        extras = payload.get("extra_columns") or []
        if extras:
            lines.append(f"user cols:  {', '.join(extras)}")
        categories = payload.get("categories") or {}
        if categories:
            lines.append("categories: " + ", ".join(f"{k} ({v})" for k, v in categories.items()))
        tags = payload.get("tags") or {}
        if tags:
            lines.append("tags:       " + ", ".join(f"{k} ({v})" for k, v in tags.items()))
        return "\n".join(lines)
