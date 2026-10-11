---
id: TASK-18
title: 'Epic: leave-one-out review of every rule'
status: To Do
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-11 21:31'
labels:
  - epic
  - benchmark
dependencies: []
priority: high
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-11: remove each rule on its own and judge the effect; a rule whose removal improves the scores is a removal candidate. The usefulness check (TASK-11.15) dropped only the 30 most-firing rules, as probes of the datasets; this covers every rule that fires on any dataset, judged with the bench's verdicts (strict, within tolerance, rejected) on the full data and on dev/check. Caveat: a dataset cannot show what a rule protects that no dataset holds (a vendor token, German addresses), so a removal candidate needs a real-use note before it becomes a plugin change, which waits for the user's approval.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every rule that fired in the baseline has a judged disable mutation
- [ ] #2 A ranked report: strict and within-tolerance removals with per-dataset deltas, and the rules whose removal hurts most (the ones that earn their place)
- [ ] #3 Removal candidates become plugin tasks with a real-use note, waiting for the user's approval
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:31
---
Paused 2026-10-11 (user): the move from gitleaks to Betterleaks (TASK-19) runs first, so leave-one-out runs once, on the new rule set. TASK-19.7 re-baselines and restarts it.
---
<!-- COMMENTS:END -->
