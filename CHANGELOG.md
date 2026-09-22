# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.1] — 2026-09-22

### Fixed
- The shared background service no longer restarts forever after the plugin is
  uninstalled: launchd/systemd keep it alive only while its launcher file exists.
- `promptlib list --full` and `search --full` now print prompt bodies.
- `promptlib import` reports a missing file, invalid JSON, or a non-object entry
  as an error instead of a Python traceback.
- The first-run notice prints the full path of the `stop` command.

### Changed
- README: installation through the RedJay marketplace; an accurate account of
  what the shared service installs and registers, when `prompts.csv` is created,
  and how to remove the service.
- Docs: `--json` goes before the subcommand; `id`/`created_at`/`updated_at` are
  dropped (not rejected) in updates; internal references removed.
- Removed unused code (`LibraryPaths.home`/`backup_directory`,
  `PromptLibraryService.strategy_name`, `PromptRepository.find`/`ids`).

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
