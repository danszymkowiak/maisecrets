---
id: TASK-21.8
title: >-
  Scoring and verdict: floors first, then weighted FP per 1,000 tokens (test
  first)
status: Done
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-12 00:12'
labels:
  - benchmark
  - tdd
dependencies:
  - TASK-21.6
  - TASK-21.7
parent_task_id: TASK-21
priority: high
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Change bench/maisecrets_bench/score.py and the round and mutate runners: count tokens per sample, report recall per type on valid gold with its lower bound and floor status (clears, gap, too few), FP per 1,000 tokens per dataset and weighted. New verdicts: accepted (every enforced floor holds or improves, gaps no worse, weighted FP/1k lower or equal), rejected (a floor broken or a gap worse), and neutral. Ranking by the weighted FP/1k change. The report names the type and dataset that decided a rejection, and lists every miss of a critical type.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Unit tests first for each verdict, the gap rule, the too-few rule and the weighting
- [x] #2 A round report shows per-type floor status, FP per 1,000 tokens per dataset, and the misses of each critical type
- [x] #3 The old strict and tolerance verdicts appear only as a comparison column, or are removed
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
maisecrets_bench/floorscore.py (pure, tests first): recall per scoring type on valid gold pooled over the scored datasets, one-sided 95% Wilson bound, status clears / gap / too_few / no_regression / none; false positives per 1,000 whitespace tokens per dataset and the weighted objective (floors.toml weights, guards left out); guards must not lose a find or gain a false positive; critical misses as positions. Verdict: rejected (a cleared floor broken, a gap worse, a no-regression type or a guard worse; decided_by names type and datasets), accepted (none of that and the objective falls or a gap narrows), neutral. mutate.evaluate and round.judge use it (round: the worse of dev and check); the earlier strict/tolerance verdict and mean change stay as comparison columns. run.py writes the floor table, FP/1k per dataset and critical-miss counts into report.md and metrics.json, positions into critical_misses.tsv; round.py writes dev-report.md. Baseline 20261012-020214: every type is a gap (US_SSN 99.5% closest), objective 0.291 FP/1k; smoke round on drop-uk-postcode works end to end.
<!-- SECTION:FINAL_SUMMARY:END -->
