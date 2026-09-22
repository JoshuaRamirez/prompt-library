# Contributing

Issues and pull requests are welcome.

## Ground rules

- **Standard library only** in `lib/`, `server/`, `hooks/`, and `bin/`. The
  plugin must run with nothing but `python3` (3.9+).
- **Layering:** lower layers never import higher ones. `storage/` knows nothing
  of prompts; `domain/` knows nothing of search, rendering, the CLI or MCP. The
  CLI and MCP server both go through `PromptLibraryService`, never around it.
- **Hooks never break a session:** `hooks/session_index.py` exits 0 and prints
  nothing on any failure.
- `shared_mcp.py` is vendored from
  [shared-mcp](https://github.com/JoshuaRamirez/shared-mcp); send changes to it
  there rather than editing the copy here.

## Running the tests

```sh
python3 tests/test_promptlib.py
```

Tests use temporary directories and never touch your real library. CI runs
them on Python 3.9–3.13 on Linux and macOS.

## Commit messages

Conventional Commits, e.g. `feat(search): add tag boosting`.
