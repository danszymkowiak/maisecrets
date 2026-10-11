---
id: TASK-11.37
title: 'Bench: synthetic tax and financial document templates (de_CH, fr_CH, en_US)'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-11 21:54'
labels:
  - benchmark
  - dataset
dependencies: []
parent_task_id: TASK-11
priority: medium
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the synthetic generator (bench/maisecrets_bench/adapters/synthetic.py) with templates shaped like the user's highest-risk documents: Swiss tax declarations and Lohnausweis/certificat de salaire, bank statements and MT940/CSV exports, US W-2/1099-style forms, invoices. Values from generators with valid checksums (AHV/AVS 756 with EAN-13, CHE UID with mod 11, CH IBAN, US SSN shape) and negatives that look similar (amounts, dates, reference and invoice numbers, postal codes, QR-bill references). No real values, no personal names from the user's life. Unlike the existing synthetic set, it is scored, with extra weight (user, 2026-10-11), although it is tuned to our own generator; TASK-21.1 records that caveat.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Templates in de_CH, fr_CH and en_US with injected positives and look-alike negatives, generated deterministically from a seed
- [ ] #2 The set runs as a scored dataset with the weight decided in TASK-21.1, and its first baseline numbers are recorded
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:54
---
User, 2026-10-11: the tax templates become a scored dataset with extra weight in the false-positive objective (epic TASK-21), not guard-only. Include MT940 :86: subfields (?30 BIC, ?31 IBAN, ?32 name), which the IBAN rule misses today (TASK-22).
---
<!-- COMMENTS:END -->
