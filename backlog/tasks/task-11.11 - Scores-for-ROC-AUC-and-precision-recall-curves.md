---
id: TASK-11.11
title: Scores for ROC/AUC and precision-recall curves
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 14:55'
labels:
  - benchmark
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: low
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Where a rule has a score (Presidio score, entropy, context words), expose it per match in the bench, and report PR curves / AUC per dataset; binary rules stay single points.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 AUC reported where scores exist, marked n/a elsewhere
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/curves.py (pure: sweep, auc over precision vs retained, at, gate_points; 5 tests) and bench/curves.py: a relaxing mutation built from rule_index (entropy 0; score 1.0 and require_context off for context-gated rules), one full relaxed run, each candidate's entropy or nearby-context flag, classified with score.classify. Writes curves.md into the run. First result (ai4privacy, CredData, Gretel; 4.7 min): entropy thresholds are near their best (generic-api-key 85.4% at 3.5 vs 85.6% at 3.46; jwt could rise to 5.38 for 99.2%); context gates help most rules (us-bank 215 TP / 2,179 FP with, 1,077 / 17,988 without); it-vat-code and de-plz show higher precision without the gate, but their 'true positives' are overlaps of any in-scope type, to be checked before a change. Rules without a judged candidate are n/a. 116 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
