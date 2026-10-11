---
id: TASK-18.2
title: 'Leave-one-out: ranked report and removal candidates'
status: To Do
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-11 21:31'
labels:
  - benchmark
dependencies:
  - TASK-18.1
  - TASK-19.7
parent_task_id: TASK-18
priority: high
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rank the leave-one-out results: removals that pass (strict, then within tolerance) by mean change, and the rules whose removal costs most. For each passing removal, a real-use note (what the rule protects that the datasets lack) and a plugin task waiting for the user's approval.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Report section in docs/BENCHMARK.md or the task's final summary
- [ ] #2 Plugin tasks for the candidates, each with its real-use note
<!-- AC:END -->
