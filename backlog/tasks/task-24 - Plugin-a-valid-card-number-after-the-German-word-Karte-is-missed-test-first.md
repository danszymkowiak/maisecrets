---
id: TASK-24
title: 'Plugin: a valid card number after the German word Karte is missed (test first)'
status: Done
assignee: []
created_date: '2026-10-11 23:25'
updated_date: '2026-10-12 08:31'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-21.8
  - TASK-30
priority: medium
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the findocs dataset (TASK-11.37, run 20261012-011327): 'Karte 4076 3110 3895 8940 Bezug Bancomat' in the kontoauszug_de template (language de) is missed 300 of 300, while the same generator's Luhn-valid numbers are found in English invoices. Likely the card rule's context words or the German group's regions. A rule change: phase 3, judged by TASK-21.8's verdict.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A unit test with a Luhn-valid card number after 'Karte' goes red first, then green
- [x] #2 findocs CARD recall in de_CH before and after; no floor broken (TASK-21.8)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Cause: the card rule is Presidio's weak pattern (score 0.3) and needs a context word; its words were English only. detect.PRESIDIO_EXTRA_CONTEXT adds card words of the label languages (karte, kreditkarte, kartennummer, debitkarte, bankkarte, ec-karte, girocard, carte, carta, tarjeta, creditcard, kaart, cartão, karta); Luhn still decides; short ambiguous words (kort) left out. tests/test_card_context.py red first. Run 20261012-102454 against 20261012-100249: findocs CARD 50% -> 100% (the 300 de_CH statements), Gretel CARD 36.3% -> 44.7%, +1 false positive on Gretel; TASK-21.8 verdict accepted, no floor broken.
<!-- SECTION:FINAL_SUMMARY:END -->
