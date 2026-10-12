---
id: TASK-34.1
title: 'redact: package skeleton, CLI and design note (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - redact
  - tdd
dependencies: []
parent_task_id: TASK-34
priority: high
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
redact/ as its own uv project (pyproject, tests, README) like bench/: depends on the repository's maisecrets package by path, never the other way. Entry point 'redact' (console script; uv tool install ./redact puts it on PATH). One pipeline in pure functions (functional core): extract(path) -> Document (text plus a map back to page / sheet / row / column) -> detect (deterministic, then models) -> decide (vote, review) -> render. docs/REDACT.md: purpose, what it never does, layout, the decisions below. The project's checks list in CLAUDE.md gains the tool's test command.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 redact --help and redact --version work; uv run --project redact python -m unittest discover -s redact/tests passes
- [ ] #2 A test fails if maisecrets/ or hooks/ imports anything from redact/, or if the plugin's dependencies change
- [ ] #3 docs/REDACT.md and the checks list in CLAUDE.md name the tool and its test command
<!-- AC:END -->
