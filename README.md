# prompt-library

A user-scoped, locally installed Claude Code plugin. Stores prompts in a single
CSV table keyed by `id`, and exposes them to Claude as MCP tools, to the shell as
a CLI, and to the session as slash commands.

The plugin itself is standard-library Python: no install step, no dependencies.
(The optional shared-service launcher fetches one package; see
[What it does to your machine](#what-it-does-to-your-machine).)

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 or newer, available as `python3`
- macOS or Linux. Windows is not supported: file locking uses `fcntl`.

## Install

Clone into Claude Code's skills directory; it auto-loads as
`prompt-library@skills-dir`:

```sh
git clone https://github.com/JoshuaRamirez/prompt-library ~/.claude/skills/prompt-library
```

Then, inside Claude Code:

```
/reload-plugins                                   # load without restarting
claude plugin disable prompt-library@skills-dir   # turn off
```

## What it does to your machine

- Creates `~/.claude/prompt-library/prompts.csv` on first write.
- Adds a SessionStart hook that injects a one-line-per-prompt index into each
  session (silent while the library is empty).
- Runs its MCP server as one shared background service per machine — see
  [below](#how-this-plugin-runs-its-mcp-server-shared-background-service).
  Set `SHARED_MCP_DISABLE=1` to run a private copy per session instead.

Network use is limited to one step: setting up the shared service installs the
`mcp` package (`mcp>=1.10,<2`) from PyPI into `~/.local/state/shared-mcp/venv`.
With `SHARED_MCP_DISABLE=1`, or if that install fails, nothing is fetched and
the server runs on the standard library alone. The shared service listens on
`127.0.0.1` only. Your prompts never leave the machine.

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

```sh
~/.claude/skills/prompt-library/bin/promptlib --help
```

Optionally put it on `$PATH`:

```sh
ln -s ~/.claude/skills/prompt-library/bin/promptlib ~/.local/bin/promptlib
```

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
tests/         43 unittest cases, stdlib only
docs/          SCHEMA.md, VECTOR-DB.md, diagrams/ (interactive D3)
```

Lower layers know nothing of higher ones. The CLI and MCP server are two
renderings of one service, never two implementations.

## Diagrams

`docs/diagrams/index.html` shows the plugin in three interactive D3 diagrams, all
traced from the source: control flow per use case (Sankey), each use case broken
into scenarios and steps (circle packing), and the data model (sunburst). Open it
in a browser; D3 loads from jsDelivr.

## Tests

```sh
python3 ~/.claude/skills/prompt-library/tests/test_promptlib.py
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
`SHARED_MCP_DISABLE=1` in your environment; to remove the service run
`python3 <plugin>/shared_mcp.py stop --name prompt-library`. State, logs and the service definition live under
`~/.local/state/shared-mcp/prompt-library/`. The kit is the single file `shared_mcp.py` vendored into this plugin; source, tests and design notes: https://github.com/JoshuaRamirez/shared-mcp

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are recorded in
[CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2026 Joshua Ramirez
