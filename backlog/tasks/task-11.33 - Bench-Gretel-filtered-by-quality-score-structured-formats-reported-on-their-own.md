---
id: TASK-11.33
title: >-
  Bench: Gretel filtered by quality score, structured formats reported on their
  own
status: Done
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-11 22:56'
labels:
  - benchmark
  - dataset
dependencies: []
parent_task_id: TASK-11
priority: high
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Gretel adapter (bench/maisecrets_bench/adapters/gretel.py) keeps every record. The dataset has quality_score (80-95, median 90 on test) and document_type. A study that used it dropped rigidly structured formats (CSV, EDI, SWIFT, FIX, BAI, XBRL, FpML, MT940) and records below 90 quality. Here the structured formats are not dropped but reported as their own group, since bank and tax exports look like MT940 and CSV, which is the user's highest-risk content. Records below 90 are dropped. Known weakness to keep in mind when reading results: low value diversity (John Doe, janedoe@mail.com).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Records below quality 90 are dropped, with the count reported by setup
- [x] #2 Scores are reported for structured and unstructured formats separately, as well as overall
- [x] #3 The baseline is re-run and the change in Gretel numbers recorded in docs/BENCHMARK.md
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Gretel records below quality_score 90 are dropped and counted (setup: below_quality_90 = 14,008 of 55,940). Samples carry tags (schema field, read as none from older files); Gretel tags format:structured for CSV, EDI, SWIFT, FIX, BAI, XBRL, FpML, MT940 and format:unstructured otherwise; run.py scores each tag apart in metrics.json and report.md. Baseline run 20261012-005108: Gretel F1 68.6% -> 68.7%; structured 42.2% precision / 49.9% recall against 85.8% / 66.6% unstructured, with us-bank raising 2,663 of the structured 3,233 false alarms. Recorded in docs/BENCHMARK.md, Gretel.
<!-- SECTION:FINAL_SUMMARY:END -->
