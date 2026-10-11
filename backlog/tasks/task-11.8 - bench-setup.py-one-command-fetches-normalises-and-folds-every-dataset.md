---
id: TASK-11.8
title: 'bench/setup.py: one command fetches, normalises and folds every dataset'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:45'
labels:
  - benchmark
dependencies:
  - TASK-11.4
  - TASK-11.5
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->
