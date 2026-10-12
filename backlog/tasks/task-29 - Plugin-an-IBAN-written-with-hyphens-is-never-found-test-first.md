---
id: TASK-29
title: 'Plugin: an IBAN written with hyphens is never found (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 06:37'
labels:
  - detection
  - tdd
dependencies: []
references:
  - maisecrets/detect.py
priority: high
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found during TASK-22 (2026-10-12). The vendored IBAN regex takes [ -] between the groups, but _iban_ok strips only spaces: 'DE89-3704-0044-0532-0130-00' gives int() a '-', the ValueError is read as a failed check, and the IBAN reaches the model. Strip hyphens too (and judge on the bench: IBAN is a critical type).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test first: a hyphenated valid IBAN is found, a hyphenated mod-97 failure is not
- [ ] #2 Judged on the bench: IBAN recall not lower, precision unchanged
<!-- AC:END -->
