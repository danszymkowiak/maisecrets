---
id: TASK-43
title: 'Bench: why decode-and-rescan gains nothing on Mendeley''s base64 perturbation'
status: To Do
assignee: []
created_date: '2026-10-13 08:48'
labels:
  - benchmark
dependencies: []
priority: low
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From TASK-11.26: with the decode stage Mendeley's base64 recall stays at 0 % and hex rises only to 15.2 % (perturb 20261013-102211), while Gretel base64 rises from 2.1 % to 53.3 %. Find out which values are lost (length below the 24-character minimum, a context word the decoded value loses, the scorer) before the stage is switched on.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The cause is named with counts per type
<!-- AC:END -->
