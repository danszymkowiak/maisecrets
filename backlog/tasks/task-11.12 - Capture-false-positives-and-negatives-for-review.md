---
id: TASK-11.12
title: Capture false positives and negatives for review
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 12:44'
labels:
  - benchmark
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Per run, export FP/FN with rule, type, dataset, fold and masked context (shape of the value, the label words around it) for a person or an agent; local only, never committed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Export holds shapes, not values (test)
- [x] #2 Grouped by rule and by type
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/errors.py: collect() (fp detections via score.classify, misses of in-scope positives), shape() in any script, context_before() masking (non-lowercase tokens, words inside gold spans, a first word the window cut), mask_rare() (a context word stays only if >=5 sources hold it; source id dropped), summary() (FPs by rule, misses by type, with shapes and common words). score.classify() added, checked against score_sample on 500 random cases. bench/errors.py CLI (--run, --split dev|check|all). Verified on the baseline dev split (7,150 FPs, 13,552 misses): of 351,337 dev gold values of >=6 chars, the 11 that equal a context word are words >=5 sources use. Three masking leaks found and fixed on the way (cut word, non-ASCII letters, plain-word values). 101 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
