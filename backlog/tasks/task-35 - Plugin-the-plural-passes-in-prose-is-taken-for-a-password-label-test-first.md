---
id: TASK-35
title: >-
  Plugin: the plural 'passes:' in prose is taken for a password label (test
  first)
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - detection
  - false-positive
  - tdd
dependencies: []
priority: low
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-12 by the pre-commit scan on a task text: the words 'Combine the passes' followed by a colon and an ordinary word gave a ds-keyword-colon hit with that word as the value. 'passes' is a plural noun, not a credential label. Check which label matches (the denylist or a label file) and whether a whole-word rule for 'pass' fixes it without losing 'pass:', 'passwd:' or 'passphrase:'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test first: 'the passes: <word>' in prose is no hit; 'pass: <value>' still is
- [ ] #2 Judged on the bench: no floor broken, false positives not higher
<!-- AC:END -->
