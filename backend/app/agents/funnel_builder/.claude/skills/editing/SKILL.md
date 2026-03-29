---
name: editing-rules
description: Load when making edits to existing funnel files or deciding edit strategy.
---

# Editing Rules

## Read-first policy
- Always call `read_funnel_file` before editing any existing file.
- Never guess file contents or rely on stale assumptions.

## Tool decision guide
- Use `edit_funnel_file` for one contiguous targeted change.
- Use `write_funnel_file` for new files and structural rewrites.
- Use `write_funnel_file` when changes span multiple non-contiguous sections.

## Theme and copy updates
- Theme changes: edit only `theme.ts` unless user explicitly asks otherwise.
- Copy tweaks: edit the specific page file or regenerate based on source copy.

## Routing updates
- Any added/removed step requires a full `App.tsx` route rewrite.
- After `delete_funnel_file`, always remove route references in `App.tsx`.

## Failure handling
- If `edit_funnel_file` returns string-not-found, re-read file and retry with exact text.
- Keep edits surgical and deterministic.
