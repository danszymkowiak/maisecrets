---
id: TASK-11.7
title: 'Setup adapter: Gretel synthetic_pii_finance_multilingual'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:46'
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
- [x] #1 Span offsets verified against the text
- [x] #2 Licence noted in docs/BENCHMARK.md
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/maisecrets_bench/adapters/gretel.py: records() downloads train+test once into the bench cache; samples() gives one sample per document (55,940; sample/group id '<split>:<index>'), language names to ISO codes (the dataset writes 'France'; unknown name stops), pii_spans as pos gold, spans with offsets outside the text or empty dropped and counted (436). bench/labels/gretel.toml: 29 labels; in scope EMAIL, PHONE, IP (v4+v6), IBAN, CARD, SECRET (password, api_key), US_SSN, ABA_ROUTING_NUMBER; the rest OUT_OF_SCOPE. Real data: 36,919 in-scope pos spans, all samples validated, 7 s. Licence Apache-2.0 (docs/BENCHMARK.md). 43 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
