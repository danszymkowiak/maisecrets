---
id: TASK-37
title: >-
  Plugin: a cheaper guard for line unwrap (ask the rules only at a long token
  tail)
status: Done
assignee: []
created_date: '2026-10-12 15:48'
updated_date: '2026-10-13 08:47'
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
- [x] #1 unwrap adds under 10 ms on 120 KB of plain prose (bench/normtime.py)
- [x] #2 the same perturbation gain or more, judged again on the bench
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
unwrap asks the shape rules only where the token run before a break has 8 characters and both runs 24, or where the run starts right after = or : (CredData's wrapped passwords). Plain prose: +4 ms on 120 KB (was +517 ms; bench/normtime.py, idle). Perturbation: line wrap 30.6% -> 32.1% (perturb 20261013-104311), the same 141 finds as the old guard. Neutral on the datasets (mutation run 20261013-104727). Stays off with the other stages: switching on is the inbox question of TASK-11.25.
<!-- SECTION:FINAL_SUMMARY:END -->
