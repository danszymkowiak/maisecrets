---
id: TASK-24
title: 'Plugin: a valid card number after the German word Karte is missed (test first)'
status: To Do
assignee: []
created_date: '2026-10-11 23:25'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-21.8
priority: medium
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the findocs dataset (TASK-11.37, run 20261012-011327): 'Karte 4076 3110 3895 8940 Bezug Bancomat' in the kontoauszug_de template (language de) is missed 300 of 300, while the same generator's Luhn-valid numbers are found in English invoices. Likely the card rule's context words or the German group's regions. A rule change: phase 3, judged by TASK-21.8's verdict.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A unit test with a Luhn-valid card number after 'Karte' goes red first, then green
- [ ] #2 findocs CARD recall in de_CH before and after; no floor broken (TASK-21.8)
<!-- AC:END -->
