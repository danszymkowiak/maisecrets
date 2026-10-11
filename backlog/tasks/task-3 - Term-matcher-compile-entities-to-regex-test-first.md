---
id: TASK-3
title: 'Term matcher: compile entities to regex (test first)'
status: To Do
assignee: []
created_date: '2026-10-11 07:00'
labels:
  - terms
  - tdd
dependencies:
  - TASK-2
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Compile parsed entities into one case-insensitive Unicode regex; boundary = not touching a letter or digit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Standalone 'Jan' matches 'Jan', 'Jan,', '(Jan)', 'Jan's', line/cell start and end; not 'January', 'Janek', 'Dajan'
- [ ] #2 'Kowalsk*' matches Kowalski, Kowalskiego, Kowalskiej as one run; '*kowalski*' matches inside jkowalski@example.com
- [ ] #3 Case-insensitive incl. Polish letters; whitespace in a term matches spaces, tabs and line breaks
- [ ] #4 Longest variant wins: 'Jan Kowalski' is one match, not two
- [ ] #5 Regex metacharacters in a term are escaped
<!-- AC:END -->
