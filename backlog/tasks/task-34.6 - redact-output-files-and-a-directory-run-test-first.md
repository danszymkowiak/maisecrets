---
id: TASK-34.6
title: 'redact: output files and a directory run (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
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
- [ ] #1 Tests first: a generated tree with PDF, CSV, xlsx, txt and an unsupported file gives the mirrored output, the summary and the skip lines
- [ ] #2 A symlink pointing out of the tree is skipped; an output path inside the source tree is refused
<!-- AC:END -->
