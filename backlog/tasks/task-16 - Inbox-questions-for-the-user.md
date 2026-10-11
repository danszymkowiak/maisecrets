---
id: TASK-16
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 11:06'
updated_date: '2026-10-11 11:41'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 11:06
---
TASK-11.1: please review docs/BENCHMARK.md (the decisions from the brainstorm: no folds, one dev/check split for the agent loop only; FP only when a detection touches no gold-sensitive span; CredData unlabelled lines as a separate unreviewed rate; TAB annotators by union, scored for precision only; regions per sample language; inclusion = precision and recall >= baseline on every dataset). Options: (a) approve as is; (b) change a decision. I recommend (a); the build continues on it per your instruction, and a change later only touches the scorer (TASK-11.9/11.10).
---

created: 2026-10-11 11:41
---
TASK-11.6: ai4privacy pii-masking-300k is licensed for academic and non-commercial use only (LICENSE.md: 'Access ... exclusively for academic research and non-commercial purposes'; redistribution or derivative works need a written licence from licensing@ai4privacy.com; the data is watermarked). maisecrets is published by a company (mcpgate.de), so tuning its rules with this data, and the parquet conversion, may fall outside the licence. Options: (a) drop ai4privacy and rely on Gretel (Apache-2.0, finance PII, 6 languages) for PII; (b) keep it for your own local, non-commercial measurement only, never in recommendations sent upstream; (c) ask AI4Privacy for a licence first. I recommend (a) because Gretel covers the same in-scope types (email, phone, IP, password, IBAN, card) under a clear licence, and the owner must be able to run the bench without a licence question. Found so far (40k records, no values read): in scope would be EMAIL, TEL->PHONE, IP, PASS->SECRET; the ID-like labels are random digit/letter runs, so out of scope.
---
<!-- COMMENTS:END -->
