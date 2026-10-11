---
id: TASK-11.27
title: >-
  Experiment: repeat-count suppression and a small learned filter, only after
  the cheaper filters
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.20
  - TASK-11.21
  - TASK-11.22
  - TASK-11.23
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: low
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 11, the weakest evidence and the highest overfitting risk. (a) An entropy-only hit that repeats 3+ times in one sample and never next to a label is suppressed (not for prefix-shaped tokens; check the threat model, since an attacker can repeat a value). (b) A logistic regression or shallow tree over about 20 features (charset, length, normalised entropy, word coverage, label class, file extension), trained on dev only and exported as plain arithmetic in a bench filter; CredSweeper and an enterprise LR paper support the approach. Run only if the filters before it plateau; the check split decides.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Repeat-count mutation judged on dev and check
- [ ] #2 The model trains on dev only; its coefficients are a small table in the repo with no dataset value; judged on check
- [ ] #3 A written go/no-go against the plateau of the earlier filters
<!-- AC:END -->
