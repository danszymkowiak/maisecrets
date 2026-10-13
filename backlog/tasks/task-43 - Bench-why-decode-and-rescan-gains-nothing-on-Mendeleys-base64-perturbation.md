---
id: TASK-43
title: 'Bench: why decode-and-rescan gains nothing on Mendeley''s base64 perturbation'
status: Done
assignee: []
created_date: '2026-10-13 08:48'
updated_date: '2026-10-13 09:26'
labels:
  - benchmark
dependencies: []
priority: low
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From TASK-11.26: with the decode stage Mendeley's base64 recall stays at 0 % and hex rises only to 15.2 % (perturb 20261013-102211), while Gretel base64 rises from 2.1 % to 53.3 %. Find out which values are lost (length below the 24-character minimum, a context word the decoded value loses, the scorer) before the stage is switched on.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The cause is named with counts per type
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Two causes, counted on Mendeley's 400 perturbation samples. (1) A bug: decode.RUN_RE wanted 24 characters before the padding, so a 16-byte value (22 characters and ==, a 16-digit card) was never decoded; fixed test first. Pooled base64 recall with the stage 63.8% -> 71.1%, Mendeley 0% -> 15.2%, findocs 43.8% -> 72.7% (perturb 20261013-112037); the datasets verdict is unchanged (mutation run 20261013-112552). (2) By design: PHONE 410, US_SSN 473 and 124 of 357 CARD values encode to fewer than 24 characters and are not decoded; 45 decoded cards are missed unencoded too (the card rule's context gate). docs/BENCHMARK.md, Decode and rescan.
<!-- SECTION:FINAL_SUMMARY:END -->
