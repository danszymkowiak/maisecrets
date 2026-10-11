---
id: TASK-11.6
title: 'Setup adapter: ai4privacy pii-masking-300k'
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
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
HF datasets load_dataset('ai4privacy/pii-masking-300k'); privacy_mask spans -> maisecrets types (EMAIL, PHONE, IBAN, CARD, IP, ...) or out of scope; multilingual; check the licence for redistribution of derived files (we ship none: setup downloads).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Span offsets verified against source_text
- [ ] #2 Licence noted in docs/BENCHMARK.md
<!-- AC:END -->
