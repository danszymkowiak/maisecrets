---
id: TASK-18.1
title: 'Leave-one-out: generate and judge a disable mutation per firing rule'
status: To Do
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-12 12:24'
labels:
  - benchmark
dependencies:
  - TASK-19.7
parent_task_id: TASK-18
priority: high
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the newest full run's rule table (metrics.json rules, hits > 0), write one disable mutation per rule (generated into the data directory, not the repository) and judge all with bench/mutate.py: disable-only, so each reruns only its samples. Include the synthetic dataset as a guard once its baseline exists (TASK-11.19). Then judge the passing ones with round.py on dev and check.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A script or mutate.py option generates the per-rule mutations from a run; a test covers it
- [ ] #2 All firing rules judged; results.json and report.md in the data directory
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12 (TASK-19.7): run on baseline 20261012-141549 (bench/loo.py --baseline ~/.cache/maisecrets-bench/runs/20261012-141549): the rule set is now Betterleaks v1.9.0 + carried gitleaks rules + Veles; 95 rules fire, so 95 disable mutations, with Betterleaks/Veles rule IDs. The generator reads the rule IDs from that run, so no list needs editing.
<!-- SECTION:NOTES:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:31
---
Paused 2026-10-11 (user): the move from gitleaks to Betterleaks (TASK-19) runs first, so leave-one-out runs once, on the new rule set. TASK-19.7 re-baselines and restarts it.
---
<!-- COMMENTS:END -->
