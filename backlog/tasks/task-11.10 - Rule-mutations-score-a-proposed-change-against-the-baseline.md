---
id: TASK-11.10
title: 'Rule mutations: score a proposed change against the baseline'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 12:29'
labels:
  - benchmark
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: medium
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A mutation spec (add, disable or replace a rule, change a threshold or keyword list) applied in the bench only, never by editing the project; the runner scores it against the baseline per dataset and fold; the inclusion rule (equal or better on every dataset, beyond fold noise) and the equal-weight ranking by score change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A mutation that only removes hits is rejected when any dataset loses recall (test)
- [x] #2 Ranking is equal-weight across datasets (test)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/mutation.py: TOML mutations (disable / set fields / add, after a rule), applied to a copy of the rule list in each worker (plugin untouched; unknown rule or field named); judge(): accepted when no dataset loses recall, precision (where it has positives) or clean samples; roles scored/guard; overall_delta = mean score change of the scored. mutate.py: baseline from a saved full run, disable-only mutations re-run only the samples where the rule fired (exact), others re-run all; ranked report. bench/mutate.py CLI (--baseline, --guard). Six probe-based mutations in bench/mutations/: with TAB as guard only 'drop uk-postcode' is accepted (+0.39 Gretel); 'drop us-bank' rejected (+4.18 Gretel score, precision 75->87%, but 215 finds lost); trade-off question in the inbox. 23 s for all six. 90 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
