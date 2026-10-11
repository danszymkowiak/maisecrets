---
id: TASK-11.10
title: 'Rule mutations: score a proposed change against the baseline'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:16'
labels:
  - benchmark
dependencies:
  - TASK-11.9
  - TASK-11.15
parent_task_id: TASK-11
priority: medium
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A mutation spec (add, disable or replace a rule, change a threshold or keyword list) applied in the bench only, never by editing the project; the runner scores it against the baseline per dataset and fold; the inclusion rule (equal or better on every dataset, beyond fold noise) and the equal-weight ranking by score change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A mutation that only removes hits is rejected when any dataset loses recall (test)
- [ ] #2 Ranking is equal-weight across datasets (test)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->
