---
id: TASK-11.5
title: 'Setup adapter: TAB court texts'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
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
- [ ] #1 Span offsets verified against the text
- [ ] #2 Annotator merge rule documented and tested
<!-- AC:END -->
