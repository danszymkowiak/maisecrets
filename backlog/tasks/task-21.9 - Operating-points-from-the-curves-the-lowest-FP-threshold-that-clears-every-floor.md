---
id: TASK-21.9
title: >-
  Operating points from the curves: the lowest-FP threshold that clears every
  floor
status: To Do
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-11 22:45'
labels:
  - benchmark
dependencies:
  - TASK-21.8
  - TASK-19.7
parent_task_id: TASK-21
priority: medium
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bench/curves.py already gives, per entropy rule and context gate, precision against retained true positives over thresholds. Turn it into a search: for each rule, the threshold with the fewest weighted FP per 1,000 tokens such that every floor still holds (or no gap gets worse). One rule at a time first; rules interact (a dropped hit can leave the span to another rule), so the chosen set is re-checked together. Each proposed threshold becomes a mutation judged as usual.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A report lists, per rule with a curve, the current threshold, the chosen one, and the FP/1k and recall change
- [ ] #2 The chosen thresholds, applied together, are judged as one mutation and the result recorded
<!-- AC:END -->
