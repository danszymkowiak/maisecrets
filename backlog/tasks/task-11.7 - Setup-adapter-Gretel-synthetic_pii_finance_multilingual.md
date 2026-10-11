---
id: TASK-11.7
title: 'Setup adapter: Gretel synthetic_pii_finance_multilingual'
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
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
HF load_dataset('gretelai/synthetic_pii_finance_multilingual'); its pii_spans -> maisecrets types; finance documents (IBAN, card, account numbers) in several languages.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Span offsets verified against the text
- [ ] #2 Licence noted in docs/BENCHMARK.md
<!-- AC:END -->
