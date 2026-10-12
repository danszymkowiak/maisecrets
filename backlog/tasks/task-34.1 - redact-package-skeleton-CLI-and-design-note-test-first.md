---
id: TASK-34.1
title: 'redact: package skeleton, CLI and design note (test first)'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:22'
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
- [x] #1 redact --help and redact --version work; uv run --project redact python -m unittest discover -s redact/tests passes
- [x] #2 A test fails if maisecrets/ or hooks/ imports anything from redact/, or if the plugin's dependencies change
- [x] #3 docs/REDACT.md and the checks list in CLAUDE.md name the tool and its test command
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
redact/ is its own uv project (maisecrets-redact, no dependencies yet; console script redact = maisecrets_redact.cli:main; uv.lock committed like bench's). Package: paths.py finds the checkout (parent of the package, or MAISECRETS_REPO) and imports maisecrets.detect from it; pipeline.py holds the pure steps (Document with a position map, Span, Decision, detect merges detectors in text order, render replaces spans and merges overlaps; DETECTORS registry empty until TASK-34.3); cli.py answers --help/--version and refuses to write any output while no detector exists. Tests (redact/tests): the command, the refusal, the pure steps, and the boundary: maisecrets/ and hooks/ import only the standard library and themselves, never maisecrets_redact, and the repository root declares no dependency. docs/REDACT.md (purpose, what it never does, pipeline, install), redact/README.md (licence table), CLAUDE.md checks list and the pre-push ruff line include redact; .gitignore ignores redact/.venv.
<!-- SECTION:FINAL_SUMMARY:END -->
