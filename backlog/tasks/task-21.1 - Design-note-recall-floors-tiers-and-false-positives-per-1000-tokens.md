---
id: TASK-21.1
title: 'Design note: recall floors, tiers and false positives per 1,000 tokens'
status: To Do
assignee: []
created_date: '2026-10-11 21:47'
updated_date: '2026-10-12 10:04'
labels:
  - benchmark
  - design
  - docs
dependencies:
  - TASK-11.33
  - TASK-11.34
  - TASK-11.35
  - TASK-11.37
parent_task_id: TASK-21
priority: high
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rewrite "Metrics" and "Judging a change" in docs/BENCHMARK.md for the epic's rule. To settle and record:
- Floors attach to the maisecrets type (the label tables already map dataset labels to types), pooled over every dataset that labels the type, and per dataset as a check. Tiers: critical 0.999, high 0.99, default no regression, none.
- Recall is computed on valid gold only (TASK-21.6); gold that fails its type's checksum is reported apart.
- A type whose baseline is below its floor must not get worse; it is listed as a gap, ranked by distance to target, and a change that raises it counts in its favour.
- Sample size: a floor is enforced through a one-sided 95% Wilson lower bound. 0.999 needs about 3,000 positives with no miss (rule of three); below the evidence needed, the type falls back to no regression, with a note.
- The objective: false positives per 1,000 whitespace tokens, per dataset, combined with weights. Gretel and the tax templates weigh more (propose 2x; the user confirms the number). The tax templates become scored rather than guard-only (user, 2026-10-11), with the caveat that they are tuned to our own generator.
- At 0.999 the misses of a critical type are few enough to review one by one; the report lists them.
- uncertain gold spans and CredData's unreviewed rows: how each counts toward recall and false positives.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 docs/BENCHMARK.md states the floors, tiers, the below-floor rule, the sample-size rule, the weighted objective and the new verdict, with the user decisions dated
- [ ] #2 The weight for Gretel and the tax templates is confirmed by the user and recorded
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: AC 1 done (docs/BENCHMARK.md, Judging a change, 'Recall floors first, then false positives'). AC 2 waits for the user's confirmation of the 2.0 weight and the SECRET split (inbox TASK-17, comment of 2026-10-12). TASK-21.8 no longer waits on this task: the weight is a value in bench/floors.toml, not code.

2026-10-12: user confirmed the weights (Gretel, findocs 2.0) and the SECRET split as written (inbox TASK-17 #6).
<!-- SECTION:NOTES:END -->
