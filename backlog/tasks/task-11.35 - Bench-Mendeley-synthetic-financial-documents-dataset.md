---
id: TASK-11.35
title: 'Bench: Mendeley synthetic financial-documents dataset'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
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
- [ ] #1 The dataset, its licence and its label format are recorded; if the licence restricts use, the adapter is opt-in; if it forbids automated download or any use outside the authors' terms, the task closes with that note
- [ ] #2 Otherwise an adapter and a label table, and its role (scored or guard) decided after the usefulness check
<!-- AC:END -->
