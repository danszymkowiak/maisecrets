---
id: TASK-11.31
title: 'Plugin: drop the uk-postcode rule (or require its context)'
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
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 1 and 2: the only change that passes strictly on every dataset (+0.13 mean, Gretel +0.39): 360 false alarms on Gretel, no true find on any dataset. Waits for TASK-17.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uk-postcode removed, or gated so that it no longer fires without a postcode word
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
