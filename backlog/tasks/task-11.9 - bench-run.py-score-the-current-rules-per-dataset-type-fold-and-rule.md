---
id: TASK-11.9
title: 'bench/run.py: score the current rules per dataset, type, fold and rule'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:06'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->
