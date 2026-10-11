---
id: TASK-11.12
title: Capture false positives and negatives for review
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per run, export FP/FN with rule, type, dataset, fold and masked context (shape of the value, the label words around it) for a person or an agent; local only, never committed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Export holds shapes, not values (test)
- [ ] #2 Grouped by rule and by type
<!-- AC:END -->
