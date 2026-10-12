---
id: TASK-18.2
title: 'Leave-one-out: ranked report and removal candidates'
status: Done
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-12 19:36'
labels:
  - benchmark
dependencies:
  - TASK-18.1
  - TASK-19.7
parent_task_id: TASK-18
priority: high
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rank the leave-one-out results: removals that pass (strict, then within tolerance) by mean change, and the rules whose removal costs most. For each passing removal, a real-use note (what the rule protects that the datasets lack) and a plugin task waiting for the user's approval.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Report section in docs/BENCHMARK.md or the task's final summary
- [x] #2 Plugin tasks for the candidates, each with its real-use note
- [x] #3 The ranking: pure wins, then trades by weighted FP saved per TP lost (counts shown, small counts flagged), then protected rules; marginal counts from TASK-18.1
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ranking decided with the user on 2026-10-12: sort the removals by the change in true positives against the change in false positives. Refined: (1) marginal counts from leave-one-out (only finds no other rule picks up, only alarms that disappear); (2) lost true positives weighted by tier (critical >> high >> no regression), saved false positives weighted by the objective's dataset weights (Gretel and findocs 2.0); (3) three groups: pure wins (false positives saved, no true positive lost; sorted by false positives saved), trades (sorted by weighted false positives saved per true positive lost, both counts shown, small counts flagged as weak evidence), protected (removal breaks a recall floor or worsens a gap: listed, never a candidate). Each candidate keeps its real-use note and a plugin task for the user's approval.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/rank.py (pure wins, trades by weighted FP saved per weighted find lost, protected), counting finds on unscored personal data too: without them ID rules looked like pure wins. docs/BENCHMARK.md, Leave-one-out. Candidates: TASK-38 (de-vat-id#0 needs a context word) and TASK-39 (drop de-handelsregister), both accepted on the bench and waiting for the user.
<!-- SECTION:FINAL_SUMMARY:END -->
