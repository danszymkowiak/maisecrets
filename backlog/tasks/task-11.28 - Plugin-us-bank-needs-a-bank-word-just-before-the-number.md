---
id: TASK-11.28
title: 'Plugin: us-bank needs a bank word just before the number'
status: To Do
assignee: []
created_date: '2026-10-11 17:44'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-17
parent_task_id: TASK-11
priority: medium
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): bench/mutations/round1/us-bank-near.toml passes within tolerance on dev and check (+1.10 / +1.15 mean, Gretel +3.29; Gretel recall -0.17 points). The context check today accepts 'account' anywhere in the 80-before/40-after window, so finance documents pass every 8-17 digit run. Waits for the user's approval of plugin changes (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detect.py's us-bank asks for an account/bank word within 30 non-digit characters before the number, as the mutation does
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
