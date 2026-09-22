# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-09-22

First public release.

- CSV-backed prompt store with an open column set; unknown fields become columns.
- MCP tools: `prompt_search`, `prompt_list`, `prompt_get`, `prompt_add`,
  `prompt_update`, `prompt_delete`, `prompt_render`, `prompt_stats`.
- `promptlib` CLI over the same service.
- Slash commands: `/prompt-save`, `/prompt-find`, `/prompt-list`, `/prompt-use`,
  `/prompt-edit`.
- SessionStart hook that injects a compact index of stored prompts.
- Optional shared background MCP service (vendored `shared_mcp.py`).
- `docs/diagrams/`: interactive control-flow, use-case and data-model diagrams.
