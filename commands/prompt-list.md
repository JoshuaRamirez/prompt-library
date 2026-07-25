---
description: List the prompt library, optionally filtered by tag or category
argument-hint: [tag or category to filter by]
---

List the prompt library. Filter: $ARGUMENTS

1. Call `prompt_stats` to learn the current tag and category vocabulary.
2. If an argument was given, match it against that vocabulary and call
   `prompt_list` with the appropriate `tags` or `category` filter. Otherwise
   list everything.
3. Render as a table grouped by category: id, title, tags, updated date.
4. Report the total count and the CSV path underneath.
