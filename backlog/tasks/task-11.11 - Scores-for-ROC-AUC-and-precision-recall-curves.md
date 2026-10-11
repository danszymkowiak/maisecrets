---
id: TASK-11.11
title: Scores for ROC/AUC and precision-recall curves
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: low
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Where a rule has a score (Presidio score, entropy, context words), expose it per match in the bench, and report PR curves / AUC per dataset; binary rules stay single points.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AUC reported where scores exist, marked n/a elsewhere
<!-- AC:END -->
