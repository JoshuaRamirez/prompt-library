---
description: Save a prompt to the prompt library
argument-hint: [prompt text, or a description of what to save]
---

Save a prompt to the prompt library.

Material to save: $ARGUMENTS

If no argument was supplied, save the most recent prompt or prompt-shaped text
in this conversation; state which one you selected before writing.

Steps:

1. Call `prompt_search` with the gist of the material. If an existing prompt is
   substantially the same, propose `prompt_update` on it instead of adding a
   duplicate, and stop for the user's decision.
2. Otherwise call `prompt_add` with:
   - `prompt` — the text, verbatim, with reusable specifics converted to
     `{{placeholders}}` where that is clearly an improvement;
   - `title` — a short descriptive title;
   - `tags` — 2–5 retrieval tags;
   - `category` — one word, reusing an existing category from `prompt_stats`
     when a suitable one exists;
   - `source` — where it came from, if known.
   Add any further columns the material warrants; the table is open.
3. Report the assigned id, title, tags, and any detected `{{variables}}`.
