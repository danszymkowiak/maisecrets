---
id: TASK-11.25
title: 'Experiment: a normaliser with an offset map before the shape rules'
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.19
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: high
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 1 for recall (the strongest measured gap). One function returns a normalised copy of the text and an index map back to the original, so spans found in the copy redact the true text: strip ANSI/OSC and render CR overwrites; delete zero-width, soft hyphen and bidi format characters (fast path when text.isascii()); strip cat -n, grep and diff gutters; then decode HTML entities and escapes; NFKC fullwidth folding last, shape rules only (notes disagree on its value). Guarded line unwrap (join only when the joined text hits a prefix-anchored rule that neither half hits) is a separate variant, because the README records that a plain next-line join failed on .env files. The C25 term matcher needs the same function (TERMS.md). This is a plugin change behind a switch, measured on the synthetic dataset and the perturbation suite.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Recall per transform before and after, on the perturbation suite, for each normaliser stage
- [ ] #2 Precision on all datasets not lower (strict or within tolerance); added hook time on 25 KB and 120 KB synthetic input reported
- [ ] #3 The guarded-unwrap variant judged separately against .env-shaped neg spans
<!-- AC:END -->
