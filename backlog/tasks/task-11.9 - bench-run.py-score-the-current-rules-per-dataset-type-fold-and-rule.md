---
id: TASK-11.9
title: 'bench/run.py: score the current rules per dataset, type, fold and rule'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
dependencies:
  - TASK-11.8
parent_task_id: TASK-11
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
detect.scan over every sample (parallel), match against gold, report TP/FP/FN, precision, recall, F1 per dataset/type/fold, the equal-weight mean across datasets, hits per rule and the rules that never trigger. JSON for machines, markdown for people; shapes only, never values. Timing per dataset.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Metrics tested on a tiny hand-made dataset
- [ ] #2 Never-triggered rules listed
- [ ] #3 Report holds no value (test)
<!-- AC:END -->
