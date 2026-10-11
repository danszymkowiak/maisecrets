---
id: TASK-2
title: Term file parser and validation (test first)
status: Done
assignee: []
created_date: '2026-10-11 07:00'
updated_date: '2026-10-11 07:23'
labels:
  - terms
  - tdd
dependencies:
  - TASK-1
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Pure function: text of terms.txt -> list of entities (label, variants with mode). Functional core, no I/O.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tests written and red before implementation, synthetic names only (e.g. Jan Kowalski, ul. Przykladowa 12)
- [x] #2 Parses label + | separated variants; ignores blank lines and # comments; trims whitespace
- [x] #3 Parses * prefix/suffix into the four modes
- [x] #4 Rejects: missing label, bad label shape, empty variant, *x* shorter than 4, duplicate label; every error names the line number and never the term text
- [x] #5 Loader refuses a file that is group/world readable (allowing for root in CI) and fails closed with a message
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets/terms.py: pure parse(text, reserved) -> [Entity(label, variants, line)] with Variant(text, mode) in four modes (WORD/STARTS/ENDS/INSIDE) and Entity.canonical (first plain variant). Rejects bad/missing/reserved/duplicate labels, empty variants, inner *, *x* under 4 chars; errors name the line only. load(path) returns [] when missing, refuses mode & 0o077 (mode bits, so root too; skipped on Windows) with a chmod 600 hint, refuses non-UTF-8 without bytes, prefixes parse errors with the path. reserved defaults empty; TASK-4 passes the detector types. 20 tests in tests/test_terms.py; full suite, replay_can_fail, scan_tree, derived_counts, lint_plugin, ruff green; tests also pass on Python 3.9.
<!-- SECTION:FINAL_SUMMARY:END -->
