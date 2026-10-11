---
id: TASK-11.8
title: 'bench/setup.py: one command fetches, normalises and folds every dataset'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
dependencies:
  - TASK-11.4
  - TASK-11.5
  - TASK-11.6
  - TASK-11.7
parent_task_id: TASK-11
priority: medium
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Runs each adapter, writes the parquet files and a manifest (dataset versions/commits, row counts, fold seed) into the data dir; idempotent; a dataset can be skipped or pointed at an existing clone.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A second run changes nothing
- [ ] #2 Manifest records versions and counts
<!-- AC:END -->
