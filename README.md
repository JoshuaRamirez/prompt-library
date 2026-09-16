# prompt-library

A user-scoped, locally installed Claude Code plugin. Stores prompts in a single
CSV table keyed by `id`, and exposes them to Claude as MCP tools, to the shell as
a CLI, and to the session as slash commands.

Standard library Python only — no install step, no dependencies.

## Install

Already installed: the plugin lives at `~/.claude/skills/prompt-library/` and
auto-loads as `prompt-library@skills-dir`.

```
/reload-plugins                              # load without restarting
claude plugin disable prompt-library@skills-dir   # turn off
```

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
docs/          SCHEMA.md, VECTOR-DB.md
```

Lower layers know nothing of higher ones. The CLI and MCP server are two
renderings of one service, never two implementations.

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
