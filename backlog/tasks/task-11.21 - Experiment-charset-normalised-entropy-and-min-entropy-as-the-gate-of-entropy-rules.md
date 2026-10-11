---
id: TASK-11.21
title: >-
  Experiment: charset-normalised entropy and min-entropy as the gate of entropy
  rules
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-11 22:45'
labels:
  - benchmark
dependencies:
  - TASK-11.18
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 2. Raw Shannon entropy rises with length and alphabet, so one threshold per rule treats a 20-char hex value and a 60-char base64 value alike. Try entropy divided by log2 of the detected alphabet (hex, base32, base64, base64url, base62), length-corrected entropy, and min-entropy. bench/curves.py already sweeps raw thresholds: add each variant as another x-axis, pick a threshold per charset on dev, then judge it as a bench filter.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 curves.py reports area and today's point for raw, normalised and min-entropy per entropy rule of the new rule set
- [ ] #2 The best variant per charset is a mutation judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens); the threshold is chosen on dev only
- [ ] #3 Result recorded in docs/BENCHMARK.md or as a final summary, including a negative result
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12, tooling in 97b5373: maisecrets_bench/entropy.py (charset; raw, normalised, length_corrected, min entropy) and curves.py's 'Entropy variants' tables (area per variant and rule; per charset a threshold chosen on dev to keep today's dev share of true positives, read on check). curves.py has not been run with it yet; run it on the new rule set after TASK-19.7.
<!-- SECTION:NOTES:END -->
