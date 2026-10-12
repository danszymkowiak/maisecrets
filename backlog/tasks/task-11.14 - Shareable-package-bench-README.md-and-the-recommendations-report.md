---
id: TASK-11.14
title: 'Shareable package: bench/README.md and the recommendations report'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-12 12:29'
labels:
  - benchmark
  - upstream
dependencies:
  - TASK-11.10
  - TASK-11.16
  - TASK-19.7
parent_task_id: TASK-11
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The owner can run setup and the benchmark on their machine; the report lists recommended rule changes with per-dataset deltas and examples by shape, and never-triggered rules. Sharing it upstream is outward-facing: ask the user first.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fresh-clone instructions tested in a temp dir
- [x] #2 Report format agreed with the user
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: bench/README.md is a full guide (requirements, quick start, datasets with licences, commands, mutation format, what may be shared). Fresh clone in a temp dir with its own MAISECRETS_BENCH_DATA: bench tests OK, setup --only tab (cloned from GitHub), run, usefulness, mutate, errors all worked. Reports show precision n/a for a dataset without positives. Waiting on the report format (inbox TASK-16).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Report format agreed with the user on 2026-10-11 (inbox TASK-16 #10: one combined recommendations page per round). bench/recommend.py (maisecrets_bench/recommend.py) writes <data>/recommendations/<time>/recommendations.md from a baseline run and mutation runs: baseline per dataset, recall floors per type (recomputed over the shown datasets), accepted changes with per-dataset true/false hits and precision/recall, rejected or neutral ones with their reason, never-fired rules, how to reproduce. Local-only datasets (ai4privacy) never appear, values never. Tests: bench/tests/test_recommend.py; generated once from the current baseline (no ai4privacy line). Fresh-clone check done earlier (AC #1). Sharing the page upstream stays the user's step (TASK-8).
<!-- SECTION:FINAL_SUMMARY:END -->
