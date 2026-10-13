---
id: TASK-11.27
title: >-
  Experiment: repeat-count suppression and a small learned filter, only after
  the cheaper filters
status: Done
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-13 09:09'
labels:
  - benchmark
dependencies:
  - TASK-11.20
  - TASK-11.21
  - TASK-11.22
  - TASK-11.23
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: low
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 11, the weakest evidence and the highest overfitting risk. (a) An entropy-only hit that repeats 3+ times in one sample and never next to a label is suppressed (not for prefix-shaped tokens; check the threat model, since an attacker can repeat a value). (b) A logistic regression or shallow tree over about 20 features (charset, length, normalised entropy, word coverage, label class, file extension), trained on dev only and exported as plain arithmetic in a bench filter; CredSweeper and an enterprise LR paper support the approach. Run only if the filters before it plateau; the check split decides.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Repeat-count mutation judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens)
- [x] #2 The model trains on dev only; its coefficients are a small table in the repo with no dataset value; judged on check by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens)
- [x] #3 A written go/no-go against the plateau of the earlier filters
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Repeat count: repeat3 rejected (CredData false positives 2,298 -> 1,055 but 154 finds lost, Nemotron 151); repeat10 accepted on dev and check (round 20261013-105913; 353 CredData false positives counted per hit, no find repeats 10 times), but a log repeating a real password is the threat-model case it would let through: inbox question. Learned filter: logistic regression over 28 features, trained on dev only (bench/learn.py, coefficients in maisecrets_bench/learned_table.py); keeping every dev find it drops 42 of 2,021 dev false positives, accepted on dev and check but weaker than the hand filters. Go/no-go: no-go for the learned filter (docs/BENCHMARK.md, Repeat count and a learned filter).
<!-- SECTION:FINAL_SUMMARY:END -->
