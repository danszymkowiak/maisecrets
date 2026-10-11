---
id: TASK-11.5
title: 'Setup adapter: TAB court texts'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:36'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.3
parent_task_id: TASK-11
priority: medium
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
../text-anonymization-benchmark echr_{train,dev,test}.json: documents with two annotators' entity_mentions (entity_type, identifier_type DIRECT/QUASI/NO_MASK, offsets). Merge the annotators (design note), map types (CODE, maybe DATETIME/LOC) to maisecrets types or out of scope; group = doc_id; keep TAB's own split as a reference.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Span offsets verified against the text
- [x] #2 Annotator merge rule documented and tested
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/maisecrets_bench/adapters/tab.py: one sample per document from echr_{train,dev,test}.json (1,268 docs, 9.6 M chars); mentions with equal offsets merged over annotators, pos if any marked DIRECT/QUASI, neg if all NO_MASK; offsets checked against span_text (all match); bench/labels/tab.toml maps all 8 types to OUT_OF_SCOPE (precision-only dataset). TAB's own train/dev/test split is not kept: the bench split by doc_id applies. 37 bench tests OK, ruff, scan_tree green.
<!-- SECTION:FINAL_SUMMARY:END -->
