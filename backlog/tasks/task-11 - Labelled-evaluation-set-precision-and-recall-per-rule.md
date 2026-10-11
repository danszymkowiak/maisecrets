---
id: TASK-11
title: 'Labelled evaluation set: precision and recall per rule'
status: To Do
assignee: []
created_date: '2026-10-11 08:05'
labels:
  - detection
  - measurement
dependencies: []
priority: low
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Asked by the user 2026-10-11. tests/fp_corpus.py has 591 NO_HIT and 23 HIT: a gate, not a measure, and no recall. Idea: scripts/score_detector.py <dataset> prints precision/recall per rule (counts only, never values), run by hand outside the repo against external labelled sets (secrets: Samsung CredData, SecretBench/FPSecretBench; PII: ai4privacy, Presidio synthetic; i2b2/n2c2 needs a DUA). Real leaked values never enter the tree. Map each dataset's labels onto our policy (e.g. test fixtures are NO_HIT here). Every miss/false alarm found becomes a synthetic §-split case in fp_corpus.py. NEEDS USER: which datasets, licences, whether terms.txt gets its own labelled set.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Dataset choice and label mapping agreed with the user
- [ ] #2 Scorecard script prints per-rule precision/recall without printing any value
- [ ] #3 Findings land as synthetic cases in tests/fp_corpus.py
<!-- AC:END -->
