---
id: TASK-11.37
title: 'Bench: synthetic tax and financial document templates (de_CH, fr_CH, en_US)'
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
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the synthetic generator (bench/maisecrets_bench/adapters/synthetic.py) with templates shaped like the user's highest-risk documents: Swiss tax declarations and Lohnausweis/certificat de salaire, bank statements and MT940/CSV exports, US W-2/1099-style forms, invoices. Values from generators with valid checksums (AHV/AVS 756 with EAN-13, CHE UID with mod 11, CH IBAN, US SSN shape) and negatives that look similar (amounts, dates, reference and invoice numbers, postal codes, QR-bill references). No real values, no personal names from the user's life. Unlike the existing synthetic set, it is scored, with extra weight (user, 2026-10-11), although it is tuned to our own generator; TASK-21.1 records that caveat.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Templates in de_CH, fr_CH and en_US with injected positives and look-alike negatives, generated deterministically from a seed
- [x] #2 The set runs as a scored dataset and its first baseline numbers are recorded; its weight in the objective is applied by TASK-21.1/21.8 (moved there 2026-10-12: TASK-21.1 now waits on this task)
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:54
---
User, 2026-10-11: the tax templates become a scored dataset with extra weight in the false-positive objective (epic TASK-21), not guard-only. Include MT940 :86: subfields (?30 BIC, ?31 IBAN, ?32 name), which the IBAN rule misses today (TASK-22).
---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/maisecrets_bench/adapters/findocs.py: 11 templates (Lohnausweis, certificat de salaire, Steuererklaerung, releve, Kontoauszug, MT940, bank CSV, W-2, 1099-INT, invoice, QR-bill), 300 each from seed 20261012; checksums tested against published vectors (AHV 756.1234.5678.97, CHE-100.155.212, SIX QR reference, ABA 011000015, CH IBAN example). Table bench/labels/findocs.toml: AHV, UID, EIN out of scope until TASK-20. Scored, default in setup. Baseline 20261012-012544: P 100.0%, R 84.4%; the misses are three detector gaps: IBAN after MT940 ?31 (TASK-22), US phone (NXX) NXX-XXXX (TASK-23, new), card after 'Karte' (TASK-24, new).
<!-- SECTION:FINAL_SUMMARY:END -->
