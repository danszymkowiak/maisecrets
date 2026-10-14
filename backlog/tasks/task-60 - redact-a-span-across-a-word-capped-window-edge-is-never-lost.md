---
id: TASK-60
title: 'redact: a span across a word-capped window edge is never lost'
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
labels:
  - redact
dependencies: []
ordinal: 121000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14: after a cut by max_words the next window starts max_words//6 words earlier, and detector_from drops a span at offset 0 of a later window; a span that starts exactly at the new window start and reaches past the previous window's end is dropped by both. With 320 words it needs a span over 53 words, but nothing enforces the overlap against the longest span. Also a character window starting mid-word can hold max_words+1 words.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test with a small cap places a span on each possible boundary position and finds it exactly once
- [ ] #2 No window holds more than max_words words as GLiNER counts them
<!-- AC:END -->
