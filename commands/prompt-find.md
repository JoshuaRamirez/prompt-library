---
description: Search the prompt library and show the best matches
argument-hint: <search terms>
---

Search the prompt library for: $ARGUMENTS

1. Call `prompt_search` with the query (default limit 10).
2. If there are no hits, retry once with the most distinctive single term, then
   fall back to `prompt_list` so the user can see what the library actually
   holds.
3. Present the matches as a compact table: id, title, tags, score.
4. If exactly one hit is clearly dominant, call `prompt_get` on it and show the
   body as well.
5. Close by noting that the prompt can be used with `/prompt-use <id>`.
