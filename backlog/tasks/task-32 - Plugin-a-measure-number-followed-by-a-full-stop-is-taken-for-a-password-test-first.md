---
id: TASK-32
title: >-
  Plugin: a measure number followed by a full stop is taken for a password (test
  first)
status: To Do
assignee: []
created_date: '2026-10-12 08:48'
labels:
  - detection
  - false-positive
  - tdd
dependencies: []
references:
  - maisecrets/detect.py
priority: low
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-12 by the pre-commit scan during TASK-26: a token TTL label, an equals sign and a number of seconds with a full stop after it (the end of a sentence) is a ds-keyword-equal-signs hit, while the same without the full stop is dropped by the measure-number fix: it tests secret.strip(quotes).isdigit(), and a number with a full stop is not. Strip a trailing sentence full stop in that check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test first: the number with a trailing full stop after a measure label is no hit; a real value after a password label with a full stop still is
- [ ] #2 Judged on the bench: no floor broken, false positives not higher
<!-- AC:END -->
