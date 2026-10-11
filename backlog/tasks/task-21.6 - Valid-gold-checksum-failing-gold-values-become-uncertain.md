---
id: TASK-21.6
title: 'Valid gold: checksum-failing gold values become uncertain'
status: Done
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-11 23:54'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.33
  - TASK-11.34
  - TASK-11.35
  - TASK-11.37
parent_task_id: TASK-21
priority: high
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Datasets carry gold values that are not valid for their type: Gretel has 408 of 2,014 IBANs failing mod-97 (measured 2026-10-11), and CARD at 19.5% recall suggests the same for Luhn (not checked yet). Before floors are scored, each gold positive of a type with a checksum (IBAN mod-97 and country length, CARD Luhn, the German and Swiss IDs, US_SSN area/group/serial rules, ABA routing checksum) is checked with the same validator the detector uses. A failing span becomes gold = "uncertain" (it counts neither as a miss nor as a false positive), and the counts per dataset and type are reported. Spans whose boundaries include a label ("IBAN: GB40...") are trimmed to the value, or counted apart. This also serves TASK-11.24's pass-rate check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each checksummed type has its gold checked with the detector validator; failing spans become uncertain
- [x] #2 A table per dataset and type: gold positives, valid, invalid, trimmed
- [x] #3 The baseline re-run shows recall on valid gold (Gretel IBAN expected near 97.8%)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/validgold.py: gold of IBAN, CARD, US_SSN, ABA and the German IDs is checked in setup with the detector's validator (the bench's for ABA and the SSN shape); failing spans become uncertain, spans with a label or card block around a valid value are trimmed. Manifest: gold revision and gold_check counts; an entry without the revision rebuilds. All datasets rebuilt; baseline 20261012-013837. Table in docs/BENCHMARK.md, Valid gold: Gretel IBAN 96.0% on valid gold (the epic's 97.8% was before the quality filter); generated ABA numbers fail their checksum ~90%; cards stay a gap at 32% (Gretel, Nemotron). Equal-weight mean 79.8% -> 80.5%.
<!-- SECTION:FINAL_SUMMARY:END -->
