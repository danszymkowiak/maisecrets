---
id: TASK-31
title: 'Plugin: Nemotron account numbers that are valid IBANs are missed (42 of 47)'
status: To Do
assignee: []
created_date: '2026-10-12 07:55'
labels:
  - detection
  - bench
dependencies:
  - TASK-30
priority: high
ordinal: 83000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by TASK-30's baseline (run 20261012-094904): Nemotron labels account numbers written as IBANs as US_BANK_NUMBER; valid gold relabels the 47 that pass mod 97 as IBAN, and the detector finds 5. IBAN is a critical type (floor 0.999). Find out why with bench/errors.py (shapes and the words before them): a separator the pattern does not take, a glued label, the lowercase or country-length gate, or something else; then a fix test first, judged on the bench.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The cause is named from the error export (shapes, never values)
- [ ] #2 A unit test goes red first, then green; IBAN recall on Nemotron rises and no dataset's false positives rise
<!-- AC:END -->
