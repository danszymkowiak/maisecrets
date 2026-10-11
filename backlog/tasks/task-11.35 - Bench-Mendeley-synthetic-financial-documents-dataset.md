---
id: TASK-11.35
title: 'Bench: Mendeley synthetic financial-documents dataset'
status: Done
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-11 23:31'
labels:
  - benchmark
  - dataset
dependencies: []
parent_task_id: TASK-11
priority: medium
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mendeley Data, "Synthetic Dataset for PII Detection and Anonymization in Financial Documents": auditor reports, tax filings and transaction confirmations with names, SSNs, card numbers, phone numbers, emails and addresses. Small and simple but on topic. Licence and format not checked yet. The fork is public and anyone may run the bench (user, 2026-10-11), so the licence must hold for any user, not only the owner. A dataset whose terms restrict use (non-commercial, competition-only, no derivatives, an account to accept terms) is opt-in like ai4privacy: a setup flag, off by default, its terms named in bench/README.md, and the person running it accepts them. The data and anything derived from it never enter the repository (docs/BENCHMARK.md, Hygiene).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The dataset, its licence and its label format are recorded; if the licence restricts use, the adapter is opt-in; if it forbids automated download or any use outside the authors' terms, the task closes with that note
- [x] #2 Otherwise an adapter and a label table, and its role (scored or guard) decided after the usefulness check
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Mendeley Data doi 10.17632/tzrjx692jy.1, CC BY 4.0, public API with sha256 per file: adapter bench/maisecrets_bench/adapters/mendeley.py (xlsx read with the standard library, True Predictions read with ast.literal_eval, mojibake repaired so all 397,400 spans land) and table bench/labels/mendeley.toml. E-mail is out of scope: every address is on an RFC 2606 example domain the plugin skips on purpose. Default in setup; attribution in every report. Baseline 20261012-012544: P 100.0%, R 90.6%, F1 95.0% (SSN 100%, phone 93.9%, card 75.7%). Usefulness: keep, scored; the user may still drop it (inbox TASK-17).
<!-- SECTION:FINAL_SUMMARY:END -->
