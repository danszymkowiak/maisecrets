---
id: TASK-11.3
title: Unified schema writer and grouped folds
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
dependencies:
  - TASK-11.2
parent_task_id: TASK-11
priority: high
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bench/schema.py: validate rows against the schema and write one parquet per dataset. bench/folds.py: deterministic grouped stratified k-fold (group = repo/file, document, record; stratify by gold label and type) plus a held-out test split never used for rule search. k chosen by sample count (design note). Test first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Same seed, same folds
- [ ] #2 No group crosses folds or the held-out split
- [ ] #3 Label balance per fold within a tolerance (test)
<!-- AC:END -->
