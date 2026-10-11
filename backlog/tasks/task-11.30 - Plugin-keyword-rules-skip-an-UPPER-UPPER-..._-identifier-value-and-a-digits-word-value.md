---
id: TASK-11.30
title: >-
  Plugin: keyword rules skip an UPPER-UPPER-..._ identifier value and a
  digits:word value
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
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): both pass strictly on dev (CredData +1.18 and +0.10) but move nothing on check: the shapes come from a few CredData files that sit in dev. Real-use argument: an identifier constant is no secret value. Waits for TASK-17.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ds-keyword-* and generic-api-key skip the two shapes; NO_HIT corpus cases
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
