---
id: TASK-18.2
title: 'Leave-one-out: ranked report and removal candidates'
status: To Do
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-11 22:45'
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
- [ ] #1 Report section in docs/BENCHMARK.md or the task's final summary
- [ ] #2 Plugin tasks for the candidates, each with its real-use note
<!-- AC:END -->
