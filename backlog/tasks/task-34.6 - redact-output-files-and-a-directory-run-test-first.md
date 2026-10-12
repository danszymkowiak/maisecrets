---
id: TASK-34.6
title: 'redact: output files and a directory run (test first)'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:52'
labels:
  - redact
  - tdd
dependencies:
  - TASK-34.5
parent_task_id: TASK-34
priority: high
ordinal: 92000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Single file: <file>.redacted.txt next to it, or into --out. Directory (user request 2026-10-12): redact <dir> walks it (--recursive), mirrors the tree into an output directory (default <dir>.redacted/), skips unsupported types with one line each, never follows a symlink out of the tree, never writes into the source tree, and prints a summary (files, hits per type, review items). Placeholders are consistent across the whole directory run. The source is never modified or overwritten.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tests first: a generated tree with PDF, CSV, xlsx, txt and an unsupported file gives the mirrored output, the summary and the skip lines
- [x] #2 A symlink pointing out of the tree is skipped; an output path inside the source tree is refused
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
app.run_dir(): every supported file of a directory (top level, or with recursive the whole tree, symlinked folders not entered) into a mirrored output tree (default <dir>.redacted/), sharing one Placeholders across the run; unsupported types, PDFs without text and symlinks pointing out of the tree are skipped with one log line each; an output inside the source tree raises; an existing output is kept; files waiting on review are counted. DirSummary: written, review, skipped, exists, counts. The command takes a directory (--recursive/-r, --out) and prints the skip lines and a summary of counts (exit 3 when a review is open). Tests: a generated tree with PDF, CSV, xlsx, txt, an unsupported file and a symlink out of the tree; mirroring, placeholder consistency across files, skip lines, top level only, refusal inside the source, no overwrite, source unchanged, and the command end to end. docs/REDACT.md updated.
<!-- SECTION:FINAL_SUMMARY:END -->
