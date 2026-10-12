---
id: TASK-19.7
title: Re-baseline the bench on the new rule set and resume leave-one-out
status: Done
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 12:24'
labels:
  - benchmark
dependencies:
  - TASK-19.4
  - TASK-19.5
parent_task_id: TASK-19
priority: high
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After the switch and the Kingfisher additions, run a new bench baseline and record it. Then the leave-one-out review (TASK-18) continues: TASK-18.1's disable mutations are regenerated for the rules that fire now, so the review covers Betterleaks rule IDs rather than gitleaks ones.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A new baseline is recorded and docs/BENCHMARK.md points to it
- [x] #2 TASK-18.1 is updated to the new rule IDs, and TASK-18.2 can start
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Baseline 20261012-141549 (Betterleaks + carried gitleaks rules + Veles, clean gold valid4, ai4privacy continuation leads uncertain) recorded at the top of docs/BENCHMARK.md: 95 rules fire, mean 84.1%. TASK-18.1 points to it (bench/loo.py reads the firing rule IDs from the run, so its mutations are Betterleaks/Veles IDs); TASK-18.1 and then 18.2 can run.
<!-- SECTION:FINAL_SUMMARY:END -->
