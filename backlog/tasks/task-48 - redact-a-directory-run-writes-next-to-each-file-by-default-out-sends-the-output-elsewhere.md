---
id: TASK-48
title: >-
  redact: a directory run writes next to each file by default; --out sends the
  output elsewhere
status: Done
assignee: []
created_date: '2026-10-13 22:06'
updated_date: '2026-10-13 22:10'
labels:
  - redact
dependencies: []
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User, 2026-10-14: the tool takes a single file or a whole directory; with --out the redacted files go to another folder, otherwise back into the same folder. A second run must not redact its own output.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A directory run without --out writes each .redacted.txt next to its file; --out mirrors into another folder; a test for both
- [x] #2 A second run in place takes no .redacted.txt as input
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
7ae70af: default out = the source folder; *.redacted.txt skipped as input; an --out inside the tree still refused. redact tests 70 OK.
<!-- SECTION:FINAL_SUMMARY:END -->
