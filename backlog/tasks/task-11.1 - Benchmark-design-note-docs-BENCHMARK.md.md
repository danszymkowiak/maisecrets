---
id: TASK-11.1
title: Benchmark design note docs/BENCHMARK.md
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
labels:
  - benchmark
  - design
dependencies: []
parent_task_id: TASK-11
priority: high
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Before code: layout (bench/ developer-only like backlog/, datasets and parquet outside the repo under $MAISECRETS_BENCH_DATA, default ~/.cache/maisecrets-bench), the unified schema (one row per sample: dataset, sample_id, group_id, text, gold spans with label, maisecrets type, gold in {pos, neg, uncertain}, fold), matching (span overlap for span datasets; CredData line + value span), the label mapping per dataset onto maisecrets types and what is out of scope (TAB PERSON/DATETIME/ORG: no shape, only terms.txt; CredData X = uncertain, excluded), metrics (micro and per type, per dataset, per fold; equal-weight mean across datasets), the inclusion rule (no dataset worse, beyond fold noise), never-triggered rules, data hygiene (no value in the repo or a report: shapes only; scan_tree never sees the data).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 docs/BENCHMARK.md covers layout, schema, matching, label mapping, metrics, folds, inclusion rule, hygiene
- [ ] #2 The label mapping and scope decisions are confirmed by the user (inbox)
<!-- AC:END -->
