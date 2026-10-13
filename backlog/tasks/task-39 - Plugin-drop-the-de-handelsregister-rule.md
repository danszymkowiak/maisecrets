---
id: TASK-39
title: 'Plugin: drop the de-handelsregister rule'
status: Done
assignee: []
created_date: '2026-10-12 19:32'
updated_date: '2026-10-13 20:11'
labels:
  - plugin
dependencies: []
priority: low
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-18.2 (leave-one-out): its 32 Gretel hits are real commercial register numbers (HRB after an Amtsgericht) that no dataset labels, so the bench counts them false. Real use: a register number identifies a company and is public in the Handelsregister; it is no personal data and no secret, so redacting it only costs the model context. Judged: bench/mutations/round5/drop-de-handelsregister.toml accepted against 20261012-194832. Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 de-handelsregister in PRESIDIO_SKIP with its reason; a test
- [x] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Applied in 809a0a9 with TASK-38; same check state.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Applied in 809a0a9; unit tests, replay_can_fail and the bench tests pass (the bench pool fix in the next commit let them run in the sandbox). Judged on the bench in round5.
<!-- SECTION:FINAL_SUMMARY:END -->
