---
id: TASK-11.24
title: >-
  Experiment: checksums for the remaining Presidio recognizers and EU IDs, after
  a pass-rate check on gold
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies: []
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 6; continues bench/mutations/round2 (aba, it, se) and the checksum line of TASK-11.17. Candidates: PESEL, Spanish NIF/NIE, Aadhaar (Verhoeff), Finnish HETU, Canadian SIN, Dutch BSN (11-proof), French NIR, Danish CPR, Norwegian fodselsnummer, Croatian OIB, plus a date-of-birth plausibility check inside IDs that encode one. Risk first: Gretel and ai4privacy values are generated, and generated IDs often fail their checksum, so a validator could drop true finds. Measure the share of gold pos spans per rule that pass each checksum before writing the mutation. Algorithms come from a primary source with a test vector, never from memory.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A table: per rule and dataset, gold pos count and the share passing the checksum
- [ ] #2 A bench validator per ID with published test vectors; rules whose gold mostly fails are recorded as not testable here
- [ ] #3 Mutations judged on dev and check with ai4privacy opt-in only for local measurement
<!-- AC:END -->
