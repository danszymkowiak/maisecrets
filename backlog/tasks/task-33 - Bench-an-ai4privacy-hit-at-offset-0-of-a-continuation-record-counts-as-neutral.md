---
id: TASK-33
title: >-
  Bench: an ai4privacy hit at offset 0 of a continuation record counts as
  neutral
status: To Do
assignee: []
created_date: '2026-10-12 10:04'
labels:
  - bench
dependencies:
  - TASK-30
priority: medium
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided by the user 2026-10-12 (inbox TASK-17 #3). About 1,300 of ai4privacy's dev false alarms (e-mail 1,005, IP 318, phone 20; TASK-11.17 family C) are values at offset 0 of a continuation record (ids ...B, ...C) that ai4privacy's own chunking left unlabelled. The scorer leaves such a detection uncounted (neither a hit nor a false alarm), and every report that includes ai4privacy notes that its precision is a lower bound (its generator also wrote values outside the injected slots, which cannot be told apart from real false alarms without reading the text).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test first: a detection at offset 0 of a continuation record of ai4privacy is neutral; the same at offset 0 of a first record, or elsewhere, is still scored
- [ ] #2 The ai4privacy note in every report says its precision is a lower bound
- [ ] #3 A new baseline recorded in docs/BENCHMARK.md
<!-- AC:END -->
