---
id: TASK-11.3
title: Unified schema writer and the dev/check split
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:21'
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
- [x] #1 Same group_id, same split on every machine
- [x] #2 No group on both sides of the split (test)
- [x] #3 An unknown label stops the setup with the label named (test)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/maisecrets_bench: schema.py (Sample/Span/Line dataclasses, validate with errors that name sample and field but never the text, parquet write/read with an explicit Arrow schema), split.py (sha256 of salt+dataset+group_id, 70% dev, values pinned in a test), labels.py (bench/labels/<dataset>.toml, unknown label stops with its name, types checked against the detector), detector.py (imports the plugin's detector with a temp MAISECRETS_HOME and the jsonfile store; known_types() over all 19 regions = 72 types). 26 bench tests OK; ruff, scan_tree green.
<!-- SECTION:FINAL_SUMMARY:END -->
