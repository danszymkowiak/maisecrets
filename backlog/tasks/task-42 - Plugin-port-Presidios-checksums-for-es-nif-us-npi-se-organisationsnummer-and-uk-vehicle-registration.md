---
id: TASK-42
title: >-
  Plugin: port Presidio's checksums for es-nif, us-npi, se-organisationsnummer
  and uk-vehicle-registration
status: Done
assignee: []
created_date: '2026-10-13 08:48'
updated_date: '2026-10-13 10:12'
labels:
  - plugin
dependencies: []
priority: medium
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From TASK-11.24: the four bench validators (bench/maisecrets_bench/validators.py, Presidio 2.2.364 ports with its test vectors) passed the floor verdict together (mutation run 20261013-101635): 140 false positives fewer (Gretel 109, ai4privacy 21, Nemotron 10), no find lost. Port them into detect.VALIDATORS / PRESIDIO_VALIDATOR test first, extend scripts/check_validators_against_presidio.py to them, and rerun the bench. it-vat-code and nhs stay out (each loses one phone number). Waits for the user's approval (inbox).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 detect.py validates the four rules like Presidio; tests with Presidio's vectors; the differential script covers them
- [x] #2 A bench run after the change shows the 140 false positives gone and no find lost
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.py validates es-nif, us-npi, se-organisationsnummer and uk-vehicle-registration like Presidio 2.2.364 (its test vectors in tests/test_detect_rules.py; scripts/check_validators_against_presidio.py: 0 disagreements in 4,000 each) and keeps their context word, as the bench judged them. Bench run 20261013-120024 against 20261012-194832: false positives ai4privacy 4,158 -> 4,137, Gretel 5,164 -> 5,055, Nemotron 849 -> 839 (140 fewer); finds unchanged on every dataset.
<!-- SECTION:FINAL_SUMMARY:END -->
