---
id: TASK-11
title: 'Epic: benchmark harness for the detection rules (precision/recall per dataset)'
status: To Do
assignee: []
created_date: '2026-10-11 08:05'
updated_date: '2026-10-13 06:46'
labels:
  - benchmark
  - detection
  - epic
dependencies:
  - TASK-11.22
  - TASK-11.23
  - TASK-11.24
  - TASK-11.26
  - TASK-11.27
  - TASK-11.36
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User request 2026-10-11 (chat + upstream issue comment). Measure the rules against public labelled datasets, outside the project code: a setup script fetches and normalises the datasets into one schema (parquet, outside the repo); a runner scores the current rules or proposed rule mutations (precision, recall, F1; ROC/AUC where a score exists) per dataset and fold. Later an agent proposes rules from the false positives/negatives. Inclusion: a rule change is accepted only if it is equal or better on every dataset; rules that never trigger are flagged for removal; the rest are ranked by score change with every dataset weighted equally (different use cases). Folds: many grouped folds plus a held-out test set. Datasets: Samsung CredData (../CredData, values obfuscated), TAB court text (../text-anonymization-benchmark), ai4privacy/pii-masking-300k, gretelai/synthetic_pii_finance_multilingual. Everything (harness + recommendations) must be runnable by the project owner.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Dataset choice and label mapping agreed with the user
- [ ] #2 Scorecard script prints per-rule precision/recall without printing any value
- [ ] #3 Findings land as synthetic cases in tests/fp_corpus.py
- [ ] #4 Every subtask done
- [ ] #5 The owner can run setup and the benchmark from bench/README.md on a clean machine
- [ ] #6 A recommendations report ranks rule changes by equal-weight score change and lists never-triggered rules
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11: docs/BENCHMARK.md is the spec. No k folds and no held-out set: one fixed dev/check split by group_id, used by the agent loop only; people's changes are judged on all data; counts are exact, so 'beyond fold noise' does not apply. Read 'fold' in this task as 'split'. Dataset score: F1, or precision where a dataset has no in-scope positives (TAB).

2026-10-13: the epic depends on its open subtasks (11.22-11.24, 11.26, 11.27, 11.36) so it is not taken as ready work before them.
<!-- SECTION:NOTES:END -->
