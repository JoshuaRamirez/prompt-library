---
description: Retrieve a stored prompt, fill its variables, and apply it
argument-hint: <id or search terms> [variable=value ...]
---

Use a stored prompt: $ARGUMENTS

1. Resolve the target. Treat the first token as an id and call `prompt_get`; if
   that fails, call `prompt_search` on the arguments other than `name=value`
   pairs and take the top hit,
   naming which prompt was selected.
2. Collect any `name=value` pairs from the arguments as substitution values.
3. Call `prompt_render` with those values.
4. If placeholders remain unfilled, infer them from the surrounding conversation
   where that is unambiguous, and ask about the rest — one consolidated question,
   not one per variable.
5. Show the rendered prompt, then act on it as the user's instruction for this
   turn.
