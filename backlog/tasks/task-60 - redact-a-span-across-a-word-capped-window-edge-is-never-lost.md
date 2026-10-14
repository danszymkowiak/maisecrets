---
id: TASK-60
title: 'redact: a span across a word-capped window edge is never lost'
status: Done
assignee: []
created_date: '2026-10-14 07:16'
updated_date: '2026-10-14 08:17'
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
- [x] #1 A test with a small cap places a span on each possible boundary position and finds it exactly once
- [x] #2 No window holds more than max_words words as GLiNER counts them
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
windows() counts the words of each chunk itself with GLiNER's splitter (a word the chunk starts or ends inside may count twice), ends a cut chunk where its last word ends, and starts the next one max_words//6 words earlier. detector_from keeps a span at a later chunk's start only when it reaches the earlier chunk's end or beyond (the earlier chunk dropped it there), so a span of up to max_words//6 words is found once and whole. Tests: a model that labels the visible part at an edge, on all 60 positions; random text with chunks starting inside words never over the cap.
<!-- SECTION:FINAL_SUMMARY:END -->
