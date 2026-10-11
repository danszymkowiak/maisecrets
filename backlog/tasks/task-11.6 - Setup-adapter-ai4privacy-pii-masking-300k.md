---
id: TASK-11.6
title: 'Setup adapter: ai4privacy pii-masking-300k'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:41'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.3
  - TASK-16
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blocked 2026-10-11 on the licence (inbox TASK-16). Inspected by streaming 40k records into ~/.cache/maisecrets-bench/hf (no full download, no parquet written, no code committed). Fields: source_text, privacy_mask [{value,start,end,label}], id, language (full names: English, Dutch, ...), set. Proposed table if kept: EMAIL->EMAIL, TEL->PHONE, IP->IP, PASS->SECRET, everything else OUT_OF_SCOPE (IDCARD, PASSPORT, SOCIALNUMBER, DRIVERLICENSE are random runs like 9+ or A+, no country format).
<!-- SECTION:NOTES:END -->
