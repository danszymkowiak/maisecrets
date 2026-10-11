---
id: TASK-11.3
title: Unified schema writer and the dev/check split
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:06'
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
bench/schema.py: validate rows against the schema of docs/BENCHMARK.md and write one parquet per dataset. bench/split.py: one deterministic split per dataset by group_id (hash with a fixed salt): dev about 70%, check about 30%; no k folds (docs/BENCHMARK.md, 'Dev and check: no folds'). Label tables bench/labels/<dataset>.toml; an unknown label stops the setup. Test first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Same group_id, same split on every machine
- [ ] #2 No group on both sides of the split (test)
- [ ] #3 An unknown label stops the setup with the label named (test)
<!-- AC:END -->
