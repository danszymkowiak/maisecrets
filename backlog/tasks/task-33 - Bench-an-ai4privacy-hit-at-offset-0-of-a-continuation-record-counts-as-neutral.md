---
id: TASK-33
title: >-
  Bench: an ai4privacy hit at offset 0 of a continuation record counts as
  neutral
status: Done
assignee: []
created_date: '2026-10-12 10:04'
updated_date: '2026-10-12 12:09'
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
- [x] #1 A test first: a detection at offset 0 of a continuation record of ai4privacy is neutral; the same at offset 0 of a first record, or elsewhere, is still scored
- [x] #2 The ai4privacy note in every report says its precision is a lower bound
- [x] #3 A new baseline recorded in docs/BENCHMARK.md
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The ai4privacy adapter marks the first token (up to 64 non-space characters) of a continuation record (id ending in B-Z) as uncertain gold with type OUT_OF_SCOPE, unless a labelled span already starts at 0 (continuation_lead, REVISION cont1 in the dataset version). The scorer then counts a detection there as neutral. Tests: a continuation's lead is uncertain and a detection on it neutral while one elsewhere stays a false alarm; first records and labelled starts get no such span. The ai4privacy report note says its precision is a lower bound. Baseline 20261012-140543 against 20261012-135603: ai4privacy false hits 6,140 -> 4,199, precision 96.1% -> 97.3%, true hits unchanged, nothing else moves. Recorded in docs/BENCHMARK.md.
<!-- SECTION:FINAL_SUMMARY:END -->
