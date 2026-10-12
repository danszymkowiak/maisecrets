---
id: TASK-37
title: >-
  Plugin: a cheaper guard for line unwrap (ask the rules only at a long token
  tail)
status: To Do
assignee: []
created_date: '2026-10-12 15:48'
labels:
  - plugin
dependencies: []
priority: low
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-11.25 judged the guarded unwrap: wrap recall 30.6 % -> 32.1 % on the perturbation suite (+141 finds, nothing else moves), but on plain prose it asks the shape rules at every break between word characters: 25 KB +107 ms, 120 KB +517 ms (bench/normtime.py --stages unwrap, a busy machine). Ask only where the line before ends in a run of at least ~16 token characters (a wrapped token's first half), and measure again. Low value unless the guard is also widened beyond prefix-anchored secrets.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 unwrap adds under 10 ms on 120 KB of plain prose (bench/normtime.py)
- [ ] #2 the same perturbation gain or more, judged again on the bench
<!-- AC:END -->
