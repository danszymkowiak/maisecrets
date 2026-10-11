---
id: TASK-11.4
title: 'Setup adapter: Samsung CredData'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:29'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.3
parent_task_id: TASK-11
priority: medium
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read ../CredData (path configurable): meta/*.csv (68,234 lines: T 15,753, F 48,061, X 4,082) and data/ files; one sample per labelled line (LineStart..LineEnd) with the value span (ValueStart/ValueEnd; -1 = whole line, negatives only); Category -> maisecrets type mapping; group = RepoName/FileID. Decide whether unlabelled lines of the files count as negatives (design note). Values are obfuscated but keep their shape: never print one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Row counts per label match the meta files
- [x] #2 No value appears in logs or output (test)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/maisecrets_bench/adapters/creddata.py: one sample per file (12,057 samples), files above 1 MiB cut into merged windows of ±50 lines (1,194 windows); one gold span per meta row (value span, else the row's lines; empty line marked by its break), T pos / F neg / X uncertain. Changed the design from per-line gold to per-row spans (a PEM key counted 30 times otherwise); removed the lines field from the schema; spec updated. bench/labels/creddata.toml: 274 categories -> SECRET, colons escaped (scan false alarm, TASK-15). Real data: spans 15,753/48,061/4,082 = meta rows exactly, all validated, 4 s. Tests: 32 bench tests OK incl. no value in output, row accounting, windows, merge.
<!-- SECTION:FINAL_SUMMARY:END -->
