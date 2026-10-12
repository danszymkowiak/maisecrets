---
id: TASK-11.30
title: >-
  Plugin: keyword rules skip an UPPER-UPPER-..._ identifier value and a
  digits:word value
status: Done
assignee: []
created_date: '2026-10-11 17:44'
updated_date: '2026-10-12 16:25'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-19.7
parent_task_id: TASK-11
priority: medium
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): both pass strictly on dev (CredData +1.18 and +0.10) but move nothing on check: the shapes come from a few CredData files that sit in dev. Real-use argument: an identifier constant is no secret value. Waits for TASK-17.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ds-keyword-* and generic-api-key skip the two shapes; NO_HIT corpus cases
- [x] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: approved by the user (inbox TASK-17 #1). Re-judge on the clean gold (TASK-30/31) under the floor verdict (TASK-21.8) before it lands.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixes upper-dash-identifier (ds-keyword-colon, ds-keyword-equal-signs, generic-api-key via overrides.txt) and time-or-ratio (ds-keyword-colon), f2c9ee2. Re-judged on clean gold first: both accepted (mutate-r6 against 20261012-141549). Unit tests, NO_HIT corpus cases (red without the fix), replay_can_fail 108/108.
<!-- SECTION:FINAL_SUMMARY:END -->
