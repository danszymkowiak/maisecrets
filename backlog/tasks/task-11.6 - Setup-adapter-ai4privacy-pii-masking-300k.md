---
id: TASK-11.6
title: 'Setup adapter: ai4privacy pii-masking-300k'
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 14:36'
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
- [x] #1 Span offsets verified against source_text
- [x] #2 Licence noted in docs/BENCHMARK.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blocked 2026-10-11 on the licence (inbox TASK-16). Inspected by streaming 40k records into ~/.cache/maisecrets-bench/hf (no full download, no parquet written, no code committed). Fields: source_text, privacy_mask [{value,start,end,label}], id, language (full names: English, Dutch, ...), set. Proposed table if kept: EMAIL->EMAIL, TEL->PHONE, IP->IP, PASS->SECRET, everything else OUT_OF_SCOPE (IDCARD, PASSPORT, SOCIALNUMBER, DRIVERLICENSE are random runs like 9+ or A+, no country format).

User decision 2026-10-11 (chat): option (b): keep it for the user's local, non-commercial measurement; never in recommendations sent upstream; tell the plugin's owner to get AI4Privacy's permission first. Build: opt-in setup flag --with-ai4privacy, the README notice, and run/report marking it local-only.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built per the user's decision (b), 2026-10-11: adapters/ai4privacy.py (one sample per record, sample/group id '<set>:<id>', language names to codes, privacy_mask spans as pos gold, a span whose offsets miss its value dropped and counted), bench/labels/ai4privacy.toml (EMAIL, TEL->PHONE, IP, PASS->SECRET in scope; 24 labels out of scope). Opt-in: bench/setup.py --with-ai4privacy prints the licence note; run.LOCAL_ONLY puts the note into every report that includes it (run, usefulness, mutations, round). README tells the plugin's owner to get AI4Privacy's permission first. TAB dropped from the default setup and runs (run.DROPPED). Real data: 225,405 samples, 1,497,769 spans. 111 bench tests OK.
<!-- SECTION:FINAL_SUMMARY:END -->
