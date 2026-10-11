---
id: TASK-21.10
title: Re-judge the mutations accepted so far under the floor rule
status: To Do
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-11 21:54'
labels:
  - benchmark
dependencies:
  - TASK-21.8
parent_task_id: TASK-21
priority: medium
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Re-run every mutation accepted (strict or within tolerance) in rounds 1-3, including the us-bank drop (accepted within tolerance 2026-10-11 for 0.6 points of Gretel recall), under the new verdict. A change that breaks a floor or worsens a gap is flagged for the user, together with any plugin task already written from it (TASK-11.28 to 11.32).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A table of each earlier mutation: old verdict, new verdict, and the deciding type or dataset
- [ ] #2 Plugin tasks built on a mutation that now fails get a comment and wait for the user
<!-- AC:END -->
