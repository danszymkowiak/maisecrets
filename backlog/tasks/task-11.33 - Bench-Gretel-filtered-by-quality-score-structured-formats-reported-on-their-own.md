---
id: TASK-11.33
title: >-
  Bench: Gretel filtered by quality score, structured formats reported on their
  own
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
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
- [ ] #1 Records below quality 90 are dropped, with the count reported by setup
- [ ] #2 Scores are reported for structured and unstructured formats separately, as well as overall
- [ ] #3 The baseline is re-run and the change in Gretel numbers recorded in docs/BENCHMARK.md
<!-- AC:END -->
