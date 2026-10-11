---
id: TASK-11.9
title: 'bench/run.py: score the current rules per dataset, type, fold and rule'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 12:07'
labels:
  - benchmark
dependencies:
  - TASK-11.8
parent_task_id: TASK-11
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
detect.scan over every sample (parallel), match against gold, report TP/FP/FN, precision, recall, F1 per dataset/type/fold, the equal-weight mean across datasets, hits per rule and the rules that never trigger. JSON for machines, markdown for people; shapes only, never values. Timing per dataset.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Metrics tested on a tiny hand-made dataset
- [x] #2 Never-triggered rules listed
- [x] #3 Report holds no value (test)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
score.py (pure): Detection, Counts (tp/fp over detections, found/fn over in-scope positives, unreviewed for CredData, out-of-scope coverage, samples/clean, by_type, per rule, type confusion), score_sample, metrics (precision, recall, F1, clean-sample rate, score = F1 or clean rate), overall (equal weight). run.py (shell): groups samples by language, each group in worker processes with its own temp home, regions and MAISECRETS_LOCALE (same result on every machine), long samples first; summarise + markdown report; bench/run.py CLI (--only, --limit, --jobs). Design fix from the first baseline: precision is degenerate on a dataset without positives (TAB 0% for 4 FPs), so its score is the clean-sample rate (spec updated). Baseline 2026-10-11 (4 min, 16 cores): creddata 68.3% (P 73.6 R 63.8), gretel 68.6% (P 75.1 R 63.1), tab 99.7% clean; overall 78.9%. Largest error source: us-bank rule, 4,117 FPs on Gretel. 70 bench tests OK incl. no value in report/metrics.
<!-- SECTION:FINAL_SUMMARY:END -->
