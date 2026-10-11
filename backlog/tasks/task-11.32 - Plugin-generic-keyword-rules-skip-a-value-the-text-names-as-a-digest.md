---
id: TASK-11.32
title: 'Plugin: generic keyword rules skip a value the text names as a digest'
status: To Do
assignee: []
created_date: '2026-10-11 21:05'
updated_date: '2026-10-11 22:45'
labels:
  - benchmark
  - plugin
dependencies:
  - TASK-17
  - TASK-19.7
parent_task_id: TASK-11
priority: low
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-11.20: bench/mutations/round3/digest-any.toml (filters digest_label, digest_prefix, object_id on generic-api-key and the ds-* keyword rules) is accepted strictly on dev and check, no find lost, 7 false alarms removed (CredData 6, synthetic 1), mean +0.01. Small gain, low risk: a hex value of a digest length behind a digest label and no secret word, a sha256:/sha512-/h1: prefixed value, or a 24-hex ObjectId. Waits for the user's approval of plugin changes (TASK-17).

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detect.py drops such a hit on generic-api-key and the ds-* keyword rules, as the bench filters do
- [ ] #2 A can-fail belief covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
