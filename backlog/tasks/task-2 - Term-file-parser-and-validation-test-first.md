---
id: TASK-2
title: Term file parser and validation (test first)
status: To Do
assignee: []
created_date: '2026-10-11 07:00'
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
- [ ] #1 Tests written and red before implementation, synthetic names only (e.g. Jan Kowalski, ul. Przykladowa 12)
- [ ] #2 Parses label + | separated variants; ignores blank lines and # comments; trims whitespace
- [ ] #3 Parses * prefix/suffix into the four modes
- [ ] #4 Rejects: missing label, bad label shape, empty variant, *x* shorter than 4, duplicate label; every error names the line number and never the term text
- [ ] #5 Loader refuses a file that is group/world readable (allowing for root in CI) and fails closed with a message
<!-- AC:END -->
