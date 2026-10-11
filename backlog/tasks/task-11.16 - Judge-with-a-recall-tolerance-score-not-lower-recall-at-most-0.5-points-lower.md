---
id: TASK-11.16
title: >-
  Judge with a recall tolerance: score not lower, recall at most 0.5 points
  lower
status: In Progress
assignee: []
created_date: '2026-10-11 15:15'
updated_date: '2026-10-11 15:16'
labels:
  - benchmark
dependencies: []
parent_task_id: TASK-11
priority: medium
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user chose a tolerance (TASK-16, 2026-10-11): strict 'equal or better on every dataset' accepts only 'drop uk-postcode', while dropping us-bank gains +2.09 mean for -0.6 points of Gretel recall. A change passes within tolerance when, on every dataset, the score (F1, or clean rate) does not fall and recall falls by at most 0.5 points. Strict passes stay marked apart.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 mutation.judge returns 'strict', 'tolerance' or 'rejected'; the recall tolerance is a parameter (default 0.5 points), --recall-tolerance on mutate.py and round.py judge
- [x] #2 Reports show the verdict per change and rank strict and tolerance passes by mean change
- [x] #3 docs/BENCHMARK.md 'Judging a change' and bench/README.md state the rule; tests cover the boundary
<!-- AC:END -->
