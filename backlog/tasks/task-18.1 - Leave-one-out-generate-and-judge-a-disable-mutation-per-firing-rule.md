---
id: TASK-18.1
title: 'Leave-one-out: generate and judge a disable mutation per firing rule'
status: In Progress
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-11 21:31'
labels:
  - benchmark
dependencies: []
parent_task_id: TASK-18
priority: high
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From the newest full run's rule table (metrics.json rules, hits > 0), write one disable mutation per rule (generated into the data directory, not the repository) and judge all with bench/mutate.py: disable-only, so each reruns only its samples. Include the synthetic dataset as a guard once its baseline exists (TASK-11.19). Then judge the passing ones with round.py on dev and check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A script or mutate.py option generates the per-rule mutations from a run; a test covers it
- [ ] #2 All firing rules judged; results.json and report.md in the data directory
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:31
---
Paused 2026-10-11 (user): the move from gitleaks to Betterleaks (TASK-19) runs first, so leave-one-out runs once, on the new rule set. TASK-19.7 re-baselines and restarts it.
---
<!-- COMMENTS:END -->
