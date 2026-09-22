# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- A project page at https://joshuaramirez.github.io/prompt-library/, built with
  vanilla-mvc in `site/`. It has a live demo of search and fill-in that runs the
  plugin's ranking in the browser. GitHub Actions now builds, tests and publishes
  it with the diagrams.

## [0.1.2] — 2026-09-22

### Fixed
- The MCP server reported version 0.1.0; a test now ties it to `plugin.json`.
- A non-integer or non-positive `limit` (MCP tools and CLI) is rejected with a
  clear error instead of an internal failure or silently wrong results.
- `search` with `--limit` reported the number shown as the number matched; it now
  reports all matches (`matched` in the JSON payload) and how many are shown.
- An empty prompt body now says "prompt body must not be empty".

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
- Shared background MCP service, on by default (vendored `shared_mcp.py`): installs
  the `mcp` package into a venv and registers a login service. Opt out with
  `SHARED_MCP_DISABLE=1`.
- `docs/diagrams/`: interactive control-flow, use-case and data-model diagrams.
