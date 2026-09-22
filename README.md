# prompt-library

[![test](https://github.com/JoshuaRamirez/prompt-library/actions/workflows/test.yml/badge.svg)](https://github.com/JoshuaRamirez/prompt-library/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A prompt library for [Claude Code](https://claude.com/claude-code). Save the
prompts you reuse, find them again by keyword, fill in their `{{variables}}`, and
apply them. They live in one CSV file on your machine, which you can read and edit
in any spreadsheet or text editor. Claude reaches them through MCP tools, you
through slash commands or a shell CLI.

The library, CLI and MCP server are standard-library Python with no
dependencies. By default the MCP server runs as a shared background service,
which does install packages. See
[What it does to your machine](#what-it-does-to-your-machine).

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 or newer, available as `python3`. The shared background service
  needs 3.10 or newer (or [uv](https://docs.astral.sh/uv/)); on 3.9 the plugin
  runs its server directly instead.
- macOS or Linux. Windows is not supported: file locking uses `fcntl`.

## Install

From the [RedJay marketplace](https://github.com/JoshuaRamirez/claude-code-plugins),
inside Claude Code:

```
/plugin marketplace add JoshuaRamirez/claude-code-plugins
/plugin install prompt-library@RedJay
```

To hack on it instead, clone it into your skills directory. Claude Code loads
plugins there automatically, as `prompt-library@skills-dir`:

```sh
git clone https://github.com/JoshuaRamirez/prompt-library ~/.claude/skills/prompt-library
```

Run `/reload-plugins` to pick up edits without restarting.

## What it does to your machine

- Creates `~/.claude/prompt-library/prompts.csv` (and a `.lock` file beside
  it) at your first session start, when the index hook first reads the library.
- Adds a SessionStart hook that injects a one-line-per-prompt index into each
  session (silent while the library is empty).
- **By default, runs its MCP server as one shared background service per
  machine.** On first use it:
  - creates a Python environment at `~/.local/state/shared-mcp/venv` and
    installs `mcp>=1.10,<2` from PyPI into it (about 30 packages including
    dependencies), using `uv` if you have it;
  - registers a login-time service (a launchd agent on macOS, a `systemd --user`
    unit on Linux) that keeps the server running and restarts it if it exits.

  To avoid all of that, set `SHARED_MCP_DISABLE=1` in your environment before
  starting Claude Code. Each session then runs a private copy of the server on
  the standard library alone, and nothing is downloaded. Details and removal
  steps are [below](#how-this-plugin-runs-its-mcp-server-shared-background-service).

The shared service listens on `127.0.0.1` only. Your prompts never leave the
machine.

## Where the data lives

`~/.claude/prompt-library/prompts.csv` — outside the plugin directory, so
reinstalling or removing the plugin never destroys the library. Override with
`$PROMPT_LIBRARY_CSV` or `$PROMPT_LIBRARY_HOME`.

## Slash commands

| Command | Purpose |
|---|---|
| `/prompt-save` | Save a prompt (dedupe-checked against the library first) |
| `/prompt-find` | Ranked keyword search |
| `/prompt-list` | Enumerate, optionally filtered by tag or category |
| `/prompt-use` | Retrieve, fill `{{variables}}`, and apply |
| `/prompt-edit` | Update or delete |

## MCP tools

`prompt_search`, `prompt_list`, `prompt_get`, `prompt_add`, `prompt_update`,
`prompt_delete`, `prompt_render`, `prompt_stats`.

## CLI

The CLI is `bin/promptlib` inside the plugin directory:

```sh
bin/promptlib --help
bin/promptlib search code review
```

To use it anywhere, symlink it onto your `$PATH`, e.g.
`ln -s "$PWD/bin/promptlib" ~/.local/bin/promptlib` from the plugin directory.

## Structure

```
lib/promptlib/
  storage/     CsvTable, TableSchema, AtomicFileWriter, FileLock   (no prompt semantics)
  domain/      Prompt, PromptFilter, PromptRepository, prompt_schema
  search/      SearchStrategy port, KeywordSearchStrategy, Tokenizer
  rendering/   TemplateRenderer
  service.py   PromptLibraryService — the facade both adapters consume
  cli/         argparse CLI + formatters
  mcp/         stdio JSON-RPC transport, tool registry, protocol server
server/        MCP entrypoint (wired in .mcp.json)
bin/promptlib  CLI entrypoint
tests/         unittest suite, stdlib only
docs/          SCHEMA.md, VECTOR-DB.md, diagrams/ (interactive D3)
```

Lower layers know nothing of higher ones. The CLI and MCP server are two
renderings of one service, never two implementations.

## Diagrams

[**View the diagrams**](https://joshuaramirez.github.io/prompt-library/diagrams/):
three interactive D3 views of the plugin, all traced from the source. They show
control flow per use case (Sankey), each use case broken into scenarios and steps
(circle packing), and the data model (sunburst). The source is in
`docs/diagrams/`.

## Tests

```sh
python3 tests/test_promptlib.py
```

## Later

`docs/VECTOR-DB.md` records the deferred semantic-retrieval design: what a vector
backend would buy, which backends are worth the complexity, the hybrid ranking
scheme, index-freshness strategy, and an increment plan gated on beating the
lexical baseline. The `SearchStrategy` port is the seam it plugs into.

## How this plugin runs its MCP server (shared background service)

Claude Code normally starts a private copy of a plugin's MCP server for every open session. This
plugin instead runs **one shared copy per machine**: its MCP entry launches `shared_mcp.py connect`,
which on first use creates a small Python environment under `~/.local/state/shared-mcp/`, registers a
login-time background service (launchd on macOS, `systemd --user` on Linux, a detached process
elsewhere) that runs the server once and serves it to every session over HTTP on `127.0.0.1` only,
and then connects. Later sessions just connect. The first run prints a one-line notice.

If a background service cannot be set up (no network, no service manager, an unusual OS), the
original server runs directly as before — never a broken plugin. To opt out permanently set
`SHARED_MCP_DISABLE=1` in your environment. To remove the service, run `stop` with the
`shared_mcp.py` from your install (the first-run notice prints the exact command):

```sh
# marketplace install
python3 "$(ls -d ~/.claude/plugins/cache/RedJay/prompt-library/*/ | sort -V | tail -1)shared_mcp.py" stop --name prompt-library
# skills-directory install
python3 ~/.claude/skills/prompt-library/shared_mcp.py stop --name prompt-library
```

If you uninstall the plugin without doing this, the service stops restarting once its files are
gone (it is kept alive only while `shared_mcp.py` exists), but its registration stays until you
delete `~/Library/LaunchAgents/com.shared-mcp.prompt-library.plist` (macOS) or
`~/.config/systemd/user/shared-mcp-prompt-library.service` (Linux). State, logs and the service definition live under
`~/.local/state/shared-mcp/prompt-library/`. The kit is the single file `shared_mcp.py` vendored into this plugin; source, tests and design notes: https://github.com/JoshuaRamirez/shared-mcp

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are recorded in
[CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2026 Joshua Ramirez
