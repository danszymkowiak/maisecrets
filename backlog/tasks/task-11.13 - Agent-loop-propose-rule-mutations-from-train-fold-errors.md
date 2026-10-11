---
id: TASK-11.13
title: 'Agent loop: propose rule mutations from train-fold errors'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 14:40'
labels:
  - benchmark
  - agent
dependencies:
  - TASK-11.10
  - TASK-11.12
parent_task_id: TASK-11
priority: low
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
An agent reads the FP/FN of the train folds, proposes mutations, the runner scores them on the validation folds; accepted ones are re-checked once on the held-out split. Guard against overfitting (held-out used once per round).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A round produces a ranked list of accepted mutations with per-dataset deltas
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/round.py: brief() (dev scores, top-15 FP rules with definitions from detector.rule_index(), masked shapes and words, misses by type, mutation format) and judge() (evaluate on dev and on check; check returns verdict and mean change only). bench/round.py CLI (brief | judge). run.newest_full_run(): a baseline covers every default dataset without --limit (a Gretel-only load run had been taken as baseline). Fix found by the round: rules differ by region, so a mutation is validated once against all regions and applied per group with strict=False. Round 1 (7 proposals written from the brief, 23 min): dev and check agree in direction and size on all; only 'drop uk-postcode' passes the strict rule (+0.20 dev, +0.19 check). Narrowing us-bank to a context word just before the number gives +1.64/+1.73 but loses 0.17 points of Gretel recall (the rule also catches some card and routing numbers); trade-off question in the inbox. 111 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
