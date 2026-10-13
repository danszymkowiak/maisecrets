---
id: TASK-21
title: >-
  Epic: judge rule changes by recall floors per type, then fewest false
  positives
status: Done
assignee: []
created_date: '2026-10-11 21:47'
updated_date: '2026-10-13 06:46'
labels:
  - epic
  - benchmark
  - false-positive
dependencies: []
priority: high
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided with the user 2026-10-11. Constrained optimisation replaces the blended score: each maisecrets type gets a recall floor, and among the changes or operating points that clear every floor, the one with the fewest false positives per 1,000 tokens wins. A change can no longer trade a leaked IBAN for three fewer over-redactions; the cost of each error type stays explicit.

Tiers (user, 2026-10-11):
- Critical, recall >= 0.999: IBAN, CARD, US_SSN, CH_AHV (TASK-20), US_BANK_NUMBER, prefixed SECRET tokens.
- High, >= 0.99: EMAIL, PHONE, IP, ABA_ROUTING_NUMBER, German and Swiss tax and ID numbers.
- Default: no regression. Everything else, including generic SECRET (keyword passwords).
- None: names (maisecrets detects no names, only the terms file, C25).

Recall is measured on valid gold. The baseline of 2026-10-11 gave Gretel IBAN recall 77.0%, but 408 of its 2,014 gold IBANs fail mod-97 (generator inventions such as DE12 1234 5678 9012 3456 00), which the validator rightly rejects; on valid gold the recall is 1,535 / 1,570 = 97.8%. Without this rule a 0.999 floor could only be met by weakening the checksums, which raises false positives on exactly the user's financial documents.

Almost every type starts below its floor (baseline: Gretel CARD 19.5%, US_SSN 48.2%, PHONE 45.6%). A type below its floor must not get worse and is listed as a gap, ranked by distance to its target. 0.999 at 95% confidence needs about 3,000 positives with no miss, so floors are enforced through a one-sided lower bound, with a fallback to no regression where the evidence is too thin.

Weights (user, 2026-10-11): Gretel (TASK-11.33) and the synthetic tax templates (TASK-11.37) weigh more than the other datasets in the false-positive objective, because they look like the user's highest-risk content.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A mutation is judged by the floors and FP per 1,000 tokens; the old strict and tolerance verdicts are gone or shown only for comparison
- [x] #2 Every rule with a curve has a chosen operating point that clears the floors
- [x] #3 The mutations accepted so far are re-judged under the new rule
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Floors first, then weighted false positives per 1,000 tokens (TASK-21.1 design, 21.6 valid gold, 21.7 floors.toml, 21.8 floorscore.py verdict; the strict/tolerance verdict stays only as a comparison column). Operating points chosen from the curves (TASK-21.9, docs/BENCHMARK.md Operating points): credit-card without its gate plus generic-api-key at entropy 3.3, accepted together; applying them is plugin task TASK-40, waiting for the user. Earlier accepted mutations re-judged (TASK-21.10).
<!-- SECTION:FINAL_SUMMARY:END -->
