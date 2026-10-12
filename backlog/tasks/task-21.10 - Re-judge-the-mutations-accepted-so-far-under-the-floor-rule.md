---
id: TASK-21.10
title: Re-judge the mutations accepted so far under the floor rule
status: Done
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-12 19:13'
labels:
  - benchmark
dependencies:
  - TASK-21.8
  - TASK-19.7
parent_task_id: TASK-21
priority: medium
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Re-run every mutation accepted (strict or within tolerance) in rounds 1-3, including the us-bank drop (accepted within tolerance 2026-10-11 for 0.6 points of Gretel recall), under the new verdict. A change that breaks a floor or worsens a gap is flagged for the user, together with any plugin task already written from it (TASK-11.28 to 11.32).

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A table of each earlier mutation: old verdict, new verdict, and the deciding type or dataset
- [x] #2 Plugin tasks built on a mutation that now fails get a comment and wait for the user
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Table in docs/BENCHMARK.md (The earlier accepted changes under the floor rule): of the round 1-3 changes, de-vat-id#0, label-negative and the three digest filters still pass; every us-bank variant, se-personnummer and wordlike-75 now fail. Plugin tasks on a failing change: 11.28 and 11.29 (se part) closed as not applied; 11.22 noted.
<!-- SECTION:FINAL_SUMMARY:END -->
