---
id: TASK-11.29
title: 'Plugin: port Presidio''s checksums for se-personnummer and it-fiscal-code'
status: Done
assignee: []
created_date: '2026-10-11 17:44'
updated_date: '2026-10-12 16:36'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-19.7
parent_task_id: TASK-11
priority: medium
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Round 2 (TASK-11.17): Presidio validates both; the port does not. se-personnummer Luhn passes within tolerance (+0.03 / +0.05); of today's hits, TP 16/18 and FP 8/124 pass. it-fiscal-code: TP 3/3, FP 5/203 pass (judged only together with it-vat-code, which failed on generated gold; judge it alone first). Algorithms with published test vectors (TASK-11.24's rule). Waits for TASK-17.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 VALIDATORS gains se_personnummer and it_fiscal_code with published test vectors; PRESIDIO_VALIDATOR maps them
- [x] #2 A can-fail belief or corpus case covers it; unit tests, replay_can_fail and the bench rerun pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: approved by the user (inbox TASK-17 #1). Re-judge on the clean gold (TASK-30/31) under the floor verdict (TASK-21.8) before it lands.

2026-10-12, re-judged (run 20261012-173742): se-personnummer Luhn REJECTED on its own merits (US_SSN finds on Gretel 58,473 -> 58,463: the se rule's hits on SSN-shaped numbers were true finds). it-fiscal-code alone: its only reason was the 7 ai4privacy passwords TASK-35 lost (fixed, 1296085); re-judged cleanly in the queued run (mutate-r6).

AC 1 only in part, by the bench: it_fiscal_code added (published vectors RSSMRA85T10A562S, RCCMNL83S18D969H) and mapped; se_personnummer NOT added, because its check was rejected on clean gold (Gretel US_SSN 58,473 -> 58,463).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
it-fiscal-code now needs its check letter (94c1d97; accepted alone on clean gold, mutate-r6). se-personnummer's Luhn check was rejected on the bench (it cost 10 SSN finds on Gretel) and is not applied.
<!-- SECTION:FINAL_SUMMARY:END -->
