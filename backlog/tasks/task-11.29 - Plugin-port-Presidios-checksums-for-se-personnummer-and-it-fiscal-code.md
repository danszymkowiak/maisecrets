---
id: TASK-11.29
title: 'Plugin: port Presidio''s checksums for se-personnummer and it-fiscal-code'
status: To Do
assignee: []
created_date: '2026-10-11 17:44'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-17
parent_task_id: TASK-11
priority: medium
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): Presidio validates both; the port does not. se-personnummer Luhn passes within tolerance (+0.03 / +0.05); of today's hits, TP 16/18 and FP 8/124 pass. it-fiscal-code: TP 3/3, FP 5/203 pass (judged only together with it-vat-code, which failed on generated gold; judge it alone first). Algorithms with published test vectors (TASK-11.24's rule). Waits for TASK-17.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 VALIDATORS gains se_personnummer and it_fiscal_code with published test vectors; PRESIDIO_VALIDATOR maps them
- [ ] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->
