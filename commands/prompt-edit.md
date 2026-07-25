---
description: Update or delete a stored prompt
argument-hint: <id> [what to change]
---

Edit a stored prompt: $ARGUMENTS

1. Call `prompt_get` on the id. If the id does not resolve, call `prompt_search`
   and confirm the intended target before changing anything.
2. Show the current record.
3. Apply the requested change with `prompt_update`, sending only the fields that
   actually change. New facets may be sent as new columns.
4. For a deletion request, state the id and title and wait for explicit
   confirmation before calling `prompt_delete`.
5. Show the resulting record and its new `updated_at`.
