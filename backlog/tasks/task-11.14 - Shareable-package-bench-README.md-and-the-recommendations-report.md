---
id: TASK-11.14
title: 'Shareable package: bench/README.md and the recommendations report'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 15:15'
labels:
  - benchmark
  - upstream
dependencies:
  - TASK-11.10
  - TASK-11.16
parent_task_id: TASK-11
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The owner can run setup and the benchmark on their machine; the report lists recommended rule changes with per-dataset deltas and examples by shape, and never-triggered rules. Sharing it upstream is outward-facing: ask the user first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fresh-clone instructions tested in a temp dir
- [ ] #2 Report format agreed with the user
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: bench/README.md is a full guide (requirements, quick start, datasets with licences, commands, mutation format, what may be shared). Fresh clone in a temp dir with its own MAISECRETS_BENCH_DATA: bench tests OK, setup --only tab (cloned from GitHub), run, usefulness, mutate, errors all worked. Reports show precision n/a for a dataset without positives. Waiting on the report format (inbox TASK-16).
<!-- SECTION:NOTES:END -->
