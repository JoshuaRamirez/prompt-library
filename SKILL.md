---
name: prompt-library
description: Store, find, and reuse saved prompts. Use when the user says "save this prompt", "add to my prompt library", "what prompts do I have", "find my prompt for X", "reuse that prompt", "prompt library", "list my prompts", "update that prompt", "fill in this prompt template", or refers to a prompt by an id/slug. Use PROACTIVELY, without being asked, in two cases: (1) the user writes a substantial reusable instruction, template, rubric, or system prompt — offer to save it; (2) the user's request resembles a prompt already listed in the session's prompt-library index — search for it and offer to reuse rather than re-deriving the instruction from scratch.
---

# Prompt Library

A single CSV table of saved prompts, addressed by id. Backed by the
`prompt-library` MCP server; a `promptlib` CLI covers the same operations for
shell work.

## Storage

- Default file: `~/.claude/prompt-library/prompts.csv` (override with
  `$PROMPT_LIBRARY_CSV` or `$PROMPT_LIBRARY_HOME`).
- Lives outside the plugin directory, so reinstalling the plugin never touches
  the data.
- Declared columns: `id`, `title`, `prompt`, `tags`, `category`, `model`,
  `variables`, `notes`, `source`, `version`, `created_at`, `updated_at`.
- The table is **open**: any additional field written becomes a new column and
  is preserved on every subsequent read and write. Do not ask permission to add
  a facet — write it and the column appears.
- `id`, `created_at`, and `updated_at` are library-managed and cannot be set
  through an update.

## Tools

| Tool | Use for |
|------|---------|
| `prompt_search` | First move when looking for a stored prompt. Ranked keyword match over title, tags, category, body, notes. |
| `prompt_list` | Enumerating the library, or narrowing by tag / category / model. |
| `prompt_get` | Reading one prompt in full once its id is known. |
| `prompt_add` | Saving a new prompt. Only `prompt` is required. |
| `prompt_update` | Partial edit of an existing prompt. |
| `prompt_delete` | Removal. Irreversible — confirm with the user first. |
| `prompt_render` | Filling `{{placeholders}}` in a stored prompt. |
| `prompt_stats` | Library size, CSV path, column set, tag and category distributions. |

## Working rules

1. **Search before adding.** Run `prompt_search` on the gist of the new prompt.
   If a close match exists, propose `prompt_update` rather than creating a near
   duplicate.
2. **Let the id derive itself.** Omit `id` on add; a slug is generated from the
   title. Supply an explicit id only when the user names one.
3. **Always give a title and tags.** They carry most of the retrieval weight
   (title ×3, tags ×2.5, category ×2, body ×1, notes ×0.5). An untitled prompt
   is effectively unfindable.
4. **Placeholders use `{{name}}`.** The `variables` column is derived from the
   body on add and on any body update — do not maintain it by hand.
5. **Retrieve, then render.** When the user wants to *use* a stored prompt with
   specifics, call `prompt_render` rather than pasting the raw body and editing
   it yourself.
6. **Confirm deletions.** State the id and title, then wait.
7. **Report the id after every write.** It is how the user addresses the record
   next time.

## CLI

`${CLAUDE_PLUGIN_ROOT}/bin/promptlib` mirrors the tools:

```
promptlib list [--tag T]... [--category C] [--limit N] [--full]
promptlib search <query...> [--limit N] [--tag T]... [--full]
promptlib get <id> [--body-only]
promptlib add --title T --prompt TEXT [--tags a,b] [--set COLUMN=VALUE]...
promptlib update <id> [--title T] [--prompt TEXT] [--set COLUMN=VALUE]...
promptlib delete <id> [--yes]
promptlib render <id> --set name=value...
promptlib stats | promptlib path
promptlib import <file.json>        # upsert an array of records by id
```

`--prompt -` (or omitting `--prompt`) reads the body from stdin, which is the
practical way to store a multi-line prompt from the shell. `--json` on any
subcommand emits the same payload the MCP tools return.

## Extending retrieval

Search sits behind a `SearchStrategy` port (`lib/promptlib/search/`). Semantic
retrieval is a second implementation of that port, not a rewrite. See
`docs/VECTOR-DB.md` before proposing embedding work.
