---
id: TASK-11.8
title: 'bench/setup.py: one command fetches, normalises and folds every dataset'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:51'
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
- [x] #1 A second run changes nothing
- [x] #2 Manifest records versions and counts
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/setup.py: Source(name, version, build, stats); run() writes <data>/parquet/<dataset>.parquet atomically and merges manifest.json (version, samples, spans by gold, split counts, dropped, split_salt); skips a source whose version and file are present. Versions: git HEAD of the CredData/TAB checkout, HF dataset sha for Gretel. bench/setup.py CLI: --creddata, --tab (else git clone into the data dir), --only; CredData skipped with instructions when no path. ai4privacy not wired (licence, TASK-11.6). Real run: creddata 12,057 samples, tab 1,268, gretel 55,940; 15 s; second run 'up to date' for all. 48 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
