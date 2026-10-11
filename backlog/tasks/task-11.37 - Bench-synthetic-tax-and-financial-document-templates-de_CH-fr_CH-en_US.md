---
id: TASK-11.37
title: 'Bench: synthetic tax and financial document templates (de_CH, fr_CH, en_US)'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
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
Extend the synthetic generator (bench/maisecrets_bench/adapters/synthetic.py) with templates shaped like the user's highest-risk documents: Swiss tax declarations and Lohnausweis/certificat de salaire, bank statements and MT940/CSV exports, US W-2/1099-style forms, invoices. Values from generators with valid checksums (AHV/AVS 756 with EAN-13, CHE UID with mod 11, CH IBAN, US SSN shape) and negatives that look similar (amounts, dates, reference and invoice numbers, postal codes, QR-bill references). No real values, no personal names from the user's life. Like the existing synthetic set, it is a guard with no weight in the mean, because it is tuned to our own generator.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Templates in de_CH, fr_CH and en_US with injected positives and look-alike negatives, generated deterministically from a seed
- [ ] #2 The set runs as a guard in the bench and its first baseline numbers are recorded
<!-- AC:END -->
