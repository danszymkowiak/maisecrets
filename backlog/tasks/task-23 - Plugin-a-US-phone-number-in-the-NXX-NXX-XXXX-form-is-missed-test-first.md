---
id: TASK-23
title: 'Plugin: a US phone number in the (NXX) NXX-XXXX form is missed (test first)'
status: To Do
assignee: []
created_date: '2026-10-11 23:25'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-21.8
priority: medium
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the findocs dataset (TASK-11.37, run 20261012-011327): every US phone of the f1099 and invoice_en templates, written '(494) 360-7563' after 'Questions:' or a comma, is missed (600 of 600), while Swiss '+41 44 ...' numbers are found. Check the phone rule's regex and context gate on this form; Nemotron's PHONE recall is 23% too. A rule change: phase 3 (after the new metrics), judged by TASK-21.8's verdict.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A unit test with a (NXX) NXX-XXXX number in prose goes red first, then green
- [ ] #2 findocs and Nemotron PHONE recall before and after; no floor broken, weighted FP/1k not higher (TASK-21.8)
<!-- AC:END -->
