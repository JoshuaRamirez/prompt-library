#!/usr/bin/env python3
"""SessionStart hook: inject a compact index of the prompt library.

Rationale: a stored prompt that Claude does not know exists is unreachable. The
skill description can only fire on phrasings the user thinks to use; an index
makes the inventory itself visible, so recognition replaces recall.

Cost discipline — the index is always-on context, so it is kept minimal:
  * one line per prompt (id, title, tags), body never included
  * silent when the library is empty, so an unused plugin costs nothing
  * truncated past MAX_ENTRIES, with the overflow stated rather than hidden

Emits nothing and exits 0 on any failure. A hook must never obstruct a session.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

MAX_ENTRIES = 60
MAX_TITLE = 60


def build_index() -> str:
    from promptlib.service import PromptLibraryService

    service = PromptLibraryService.open()
    prompts = service.list()
    if not prompts:
        return ""

    lines = [
        f"Prompt library: {len(prompts)} stored prompt(s). "
        "Search with prompt_search, read with prompt_get, fill variables with "
        "prompt_render. Consider offering to save reusable prompts the user writes.",
        "",
    ]
    for record in prompts[:MAX_ENTRIES]:
        title = str(record.get("title") or "(untitled)")
        if len(title) > MAX_TITLE:
            title = title[: MAX_TITLE - 1] + "…"
        tags = ", ".join(record.get("tags") or [])
        suffix = f"  [{tags}]" if tags else ""
        lines.append(f"  {record.get('id', '')} — {title}{suffix}")
    overflow = len(prompts) - MAX_ENTRIES
    if overflow > 0:
        lines.append(f"  … and {overflow} more (not listed; use prompt_list to enumerate)")
    return "\n".join(lines)


def main() -> int:
    try:
        index = build_index()
    except Exception:  # noqa: BLE001 - a hook must never break a session
        return 0
    if index:
        sys.stdout.write(index + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
