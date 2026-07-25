#!/usr/bin/env python3
"""Entrypoint for the prompt-library MCP server (stdio).

Wired into .mcp.json. Standard library only — no install step.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from promptlib.mcp.server import McpServer  # noqa: E402
from promptlib.service import PromptLibraryService  # noqa: E402


def main() -> int:
    service = PromptLibraryService.open()
    McpServer(service).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
