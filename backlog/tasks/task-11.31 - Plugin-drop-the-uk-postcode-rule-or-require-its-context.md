---
id: TASK-11.31
title: 'Plugin: drop the uk-postcode rule (or require its context)'
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
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 1 and 2: the only change that passes strictly on every dataset (+0.13 mean, Gretel +0.39): 360 false alarms on Gretel, no true find on any dataset. Waits for TASK-17.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uk-postcode removed, or gated so that it no longer fires without a postcode word
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
