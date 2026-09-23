# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.3] - 2026-09-22

### Fixed
- `promptlib import` replaced every field of an existing prompt, so a record
  like `{"id": "x", "tags": "new"}` blanked x's title, text and category. An
  import now changes only the fields a record supplies. It also records a new
  text's placeholders, names the record that failed, and writes nothing when
  one fails.
- With the shared background service on, `$PROMPT_LIBRARY_CSV` and
  `$PROMPT_LIBRARY_HOME` did not reach the MCP tools, so the CLI and Claude could
  use different files. They are now forwarded.
- MCP tools:
  - "false" as a string was read as true;
  - a tags string was matched letter by letter;
  - missing required arguments were accepted.
- Updates that set `id`, `created_at` or `updated_at` were silently ignored; they
  are now refused. An empty update is an error in MCP as it was in the CLI.
- A non-UTF-8 file, or a CSV with no `id` column, gave a traceback or an empty
  listing instead of an error.
- Stats counted `Review` and `review` as different tags.

### Added
- A project page at https://joshuaramirez.github.io/prompt-library/ with a live
  demo that runs the plugin's search and fill-in in the browser. It is built with
  [vanilla-mvc](https://github.com/JoshuaRamirez/vanilla-mvc) in `site/` and
  published, with the diagrams, by GitHub Actions.
- `render` reports values no placeholder used (`unused`), which is usually a
  misspelt name. The CLI warns about these and about unfilled placeholders.
- Writes report any column they create (`new_columns`).
- `promptlib --version`, and help text for every command and option.

### Changed
- `--json` works after the command as well as before it.
- CLI errors read `promptlib: error: …` instead of exception class names. A bad
  flag shows the subcommand's usage.
- "No prompt with that id" now exits 3 instead of 2, which is argparse's code
  for a bad command line.
- `--tag` accepts commas. Listings show each tag, and untitled prompts as
  `(untitled)`. A search with no hits says so.
- Blank extra columns are left out of records.

## [0.1.2] - 2026-09-22

### Fixed
- The MCP server reported version 0.1.0; a test now ties it to `plugin.json`.
- A non-integer or non-positive `limit` (MCP tools and CLI) is rejected with a
  clear error instead of an internal failure or silently wrong results.
- `search` with `--limit` reported the number shown as the number matched; it now
  reports all matches (`matched` in the JSON payload) and how many are shown.
- Saving a prompt with an empty text now fails with "prompt body must not be
  empty".

## [0.1.1] - 2026-09-22

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

### Removed
- Unused code: `LibraryPaths.home`/`backup_directory`,
  `PromptLibraryService.strategy_name`, `PromptRepository.find`/`ids`.

## [0.1.0] - 2026-09-22

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

[Unreleased]: https://github.com/JoshuaRamirez/prompt-library/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/JoshuaRamirez/prompt-library/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/JoshuaRamirez/prompt-library/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/JoshuaRamirez/prompt-library/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JoshuaRamirez/prompt-library/releases/tag/v0.1.0
