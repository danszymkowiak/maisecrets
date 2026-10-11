---
id: TASK-21.8
title: >-
  Scoring and verdict: floors first, then weighted FP per 1,000 tokens (test
  first)
status: To Do
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-11 23:43'
labels:
  - benchmark
  - tdd
dependencies:
  - TASK-21.6
  - TASK-21.7
parent_task_id: TASK-21
priority: high
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Change bench/maisecrets_bench/score.py and the round and mutate runners: count tokens per sample, report recall per type on valid gold with its lower bound and floor status (clears, gap, too few), FP per 1,000 tokens per dataset and weighted. New verdicts: accepted (every enforced floor holds or improves, gaps no worse, weighted FP/1k lower or equal), rejected (a floor broken or a gap worse), and neutral. Ranking by the weighted FP/1k change. The report names the type and dataset that decided a rejection, and lists every miss of a critical type.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Unit tests first for each verdict, the gap rule, the too-few rule and the weighting
- [ ] #2 A round report shows per-type floor status, FP per 1,000 tokens per dataset, and the misses of each critical type
- [ ] #3 The old strict and tolerance verdicts appear only as a comparison column, or are removed
<!-- AC:END -->
