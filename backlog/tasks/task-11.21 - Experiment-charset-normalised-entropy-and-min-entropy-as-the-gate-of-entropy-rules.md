---
id: TASK-11.21
title: >-
  Experiment: charset-normalised entropy and min-entropy as the gate of entropy
  rules
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.18
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 2. Raw Shannon entropy rises with length and alphabet, so one threshold per rule treats a 20-char hex value and a 60-char base64 value alike. Try entropy divided by log2 of the detected alphabet (hex, base32, base64, base64url, base62), length-corrected entropy, and min-entropy. bench/curves.py already sweeps raw thresholds: add each variant as another x-axis, pick a threshold per charset on dev, then judge it as a bench filter.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 curves.py reports area and today's point for raw, normalised and min-entropy per gitleaks entropy rule
- [ ] #2 The best variant per charset is a mutation judged on dev and check; the threshold is chosen on dev only
- [ ] #3 Result recorded in docs/BENCHMARK.md or as a final summary, including a negative result
<!-- AC:END -->
