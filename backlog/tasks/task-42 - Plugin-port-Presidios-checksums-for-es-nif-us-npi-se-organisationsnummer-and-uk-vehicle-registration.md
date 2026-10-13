---
id: TASK-42
title: >-
  Plugin: port Presidio's checksums for es-nif, us-npi, se-organisationsnummer
  and uk-vehicle-registration
status: To Do
assignee: []
created_date: '2026-10-13 08:48'
labels:
  - plugin
dependencies:
  - TASK-17
priority: medium
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From TASK-11.24: the four bench validators (bench/maisecrets_bench/validators.py, Presidio 2.2.364 ports with its test vectors) passed the floor verdict together (mutation run 20261013-101635): 140 false positives fewer (Gretel 109, ai4privacy 21, Nemotron 10), no find lost. Port them into detect.VALIDATORS / PRESIDIO_VALIDATOR test first, extend scripts/check_validators_against_presidio.py to them, and rerun the bench. it-vat-code and nhs stay out (each loses one phone number). Waits for the user's approval (inbox).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detect.py validates the four rules like Presidio; tests with Presidio's vectors; the differential script covers them
- [ ] #2 A bench run after the change shows the 140 false positives gone and no find lost
<!-- AC:END -->
