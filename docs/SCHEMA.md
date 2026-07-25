# Storage Schema

One table, one CSV file. Default location
`~/.claude/prompt-library/prompts.csv`, overridable by `$PROMPT_LIBRARY_CSV`
(full path) or `$PROMPT_LIBRARY_HOME` (directory).

## Declared columns

| Column | Managed | Meaning |
|---|---|---|
| `id` | library | Slug identifier, derived from `title` when not supplied. Immutable after creation. |
| `title` | caller | Short descriptive name. Highest search weight. |
| `prompt` | caller | The prompt text. Required, non-empty. |
| `tags` | caller | Comma-separated retrieval tags. |
| `category` | caller | Single grouping term. |
| `model` | caller | Model the prompt is tuned for, if any. |
| `variables` | derived | `{{placeholders}}` extracted from `prompt` on write. |
| `notes` | caller | Provenance, caveats, usage guidance. |
| `source` | caller | Where the prompt came from. |
| `version` | caller | Caller-managed revision label. |
| `created_at` | library | ISO-8601 UTC, set once. |
| `updated_at` | library | ISO-8601 UTC, set on every write. |

`id`, `created_at`, and `updated_at` are refused as update inputs rather than
silently ignored at the domain boundary (`Prompt.merged_with` drops them).

## Open columns

Any field written that is not declared becomes a new CSV column and is preserved
across every subsequent read-modify-write. The library never drops a column it
did not create. Declared columns keep their fixed leading order; discovered
columns follow in first-seen order, so the file stays legible in a spreadsheet.

Callers see discovered columns as `extras` on the record.

## Integrity properties

- **Atomic replacement.** Every mutation rewrites the whole file to a sibling
  temp file, `fsync`s, and `os.replace`s over the target. An interrupted write
  leaves the previous generation intact.
- **Advisory locking.** Mutations hold an exclusive `flock` on
  `prompts.csv.lock` and re-read from disk inside the lock, so concurrent Claude
  sessions cannot clobber each other with stale in-memory state.
- **No field-size ceiling.** The CSV field limit is raised at import; long prompt
  bodies with embedded newlines, commas, and quotes round-trip exactly.
- **Strings only.** Typing lives in the domain layer, not in the file. Any tool
  that reads the CSV sees plain text.

## Why CSV

The store is deliberately the least sophisticated thing that satisfies the
requirements: one table, human-editable in any spreadsheet or text editor,
diffable in git, and readable without this plugin installed. Retrieval
sophistication is layered above it behind the `SearchStrategy` port rather than
pushed down into the storage format — see `VECTOR-DB.md`.
