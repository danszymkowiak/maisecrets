---
id: TASK-39
title: 'Plugin: drop the de-handelsregister rule'
status: To Do
assignee: []
created_date: '2026-10-12 19:32'
labels:
  - plugin
dependencies:
  - TASK-17
priority: low
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-18.2 (leave-one-out): its 32 Gretel hits are real commercial register numbers (HRB after an Amtsgericht) that no dataset labels, so the bench counts them false. Real use: a register number identifies a company and is public in the Handelsregister; it is no personal data and no secret, so redacting it only costs the model context. Judged: bench/mutations/round5/drop-de-handelsregister.toml accepted against 20261012-194832. Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 de-handelsregister in PRESIDIO_SKIP with its reason; a test
- [ ] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->
