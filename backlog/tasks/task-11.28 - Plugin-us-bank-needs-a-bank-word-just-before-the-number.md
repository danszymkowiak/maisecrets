---
id: TASK-11.28
title: 'Plugin: us-bank needs a bank word just before the number'
status: To Do
assignee: []
created_date: '2026-10-11 17:44'
updated_date: '2026-10-11 22:45'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-17
  - TASK-19.7
parent_task_id: TASK-11
priority: medium
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): bench/mutations/round1/us-bank-near.toml passes within tolerance on dev and check (+1.10 / +1.15 mean, Gretel +3.29; Gretel recall -0.17 points). The context check today accepts 'account' anywhere in the 80-before/40-after window, so finance documents pass every 8-17 digit run. Waits for the user's approval of plugin changes (TASK-17).

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detect.py's us-bank asks for an account/bank word within 30 non-digit characters before the number, as the mutation does
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
