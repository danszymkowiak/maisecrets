---
id: TASK-11.24
title: >-
  Experiment: checksums for the remaining Presidio recognizers and EU IDs, after
  a pass-rate check on gold
status: Done
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-13 08:47'
labels:
  - benchmark
dependencies:
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 6; continues bench/mutations/round2 (aba, it, se) and the checksum line of TASK-11.17. Candidates: PESEL, Spanish NIF/NIE, Aadhaar (Verhoeff), Finnish HETU, Canadian SIN, Dutch BSN (11-proof), French NIR, Danish CPR, Norwegian fodselsnummer, Croatian OIB, plus a date-of-birth plausibility check inside IDs that encode one. Risk first: Gretel and ai4privacy values are generated, and generated IDs often fail their checksum, so a validator could drop true finds. Measure the share of gold pos spans per rule that pass each checksum before writing the mutation. Algorithms come from a primary source with a test vector, never from memory.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A table: per rule and dataset, gold pos count and the share passing the checksum
- [x] #2 A bench validator per ID with published test vectors; rules whose gold mostly fails are recorded as not testable here
- [x] #3 Mutations judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens) on valid gold (TASK-21.6), with ai4privacy opt-in only for local measurement
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Seven Presidio 2.2.364 validators ported to the bench (validators.py) with Presidio's own test vectors, zero disagreement with Presidio on 20,000 random values each; medical-license left out (no published vector); PESEL, Aadhaar, HETU, SIN and the rule-less BSN, NIR, CPR, fodselsnummer, OIB never fire: not testable. bench/passrate.py: ai4privacy's IDCARD values are random, so es-nif/es-nie recall is not testable here. Floor verdict: es-nif, us-npi, se-organisationsnummer, uk-vehicle-registration accepted, together 140 false positives fewer and no find lost; es-nie neutral; it-vat-code and nhs rejected (each loses one phone number). docs/BENCHMARK.md, Presidio's remaining checksums. Porting the four: TASK-42, waits for the user.
<!-- SECTION:FINAL_SUMMARY:END -->
