---
id: TASK-11.13
title: 'Agent loop: propose rule mutations from train-fold errors'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
  - agent
dependencies:
  - TASK-11.10
  - TASK-11.12
parent_task_id: TASK-11
priority: low
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
An agent reads the FP/FN of the train folds, proposes mutations, the runner scores them on the validation folds; accepted ones are re-checked once on the held-out split. Guard against overfitting (held-out used once per round).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A round produces a ranked list of accepted mutations with per-dataset deltas
<!-- AC:END -->
