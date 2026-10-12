---
id: TASK-31
title: 'Plugin: Nemotron account numbers that are valid IBANs are missed (42 of 47)'
status: Done
assignee: []
created_date: '2026-10-12 07:55'
updated_date: '2026-10-12 08:09'
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
- [x] #1 The cause is named from the error export (shapes, never values)
- [x] #2 A unit test goes red first, then green; IBAN recall on Nemotron rises and no dataset's false positives rise
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Cause: no detector gap but a bench artefact. Valid gold shrank a value from the right until its checksum passed; a fake IBAN or card cut at a group boundary passes by chance (1 in 97, 1 in 10), so the gold became a fragment no detector reports. TASK-30's IBAN relabelling of bank numbers inherited it (47 'valid IBANs', 41 of them fragments). validgold._cut_ok: a cut only at a separator and only when the first dropped group differs in length from the last kept one (an expiry after a card is still cut off); gold valid4. Tests in bench/tests/test_validgold.py (ShrinkTests) red first. Baseline 20261012-100249 against 20261012-094904: Nemotron CARD recall 32.8% -> 95.7%, Nemotron IBAN 10.6% -> 83.3%, Gretel IBAN 95.9% -> 97.9%, Gretel CARD 32.0% -> 36.3%; no false positive moved. docs/BENCHMARK.md updated.
<!-- SECTION:FINAL_SUMMARY:END -->
