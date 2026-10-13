---
id: TASK-18
title: 'Epic: leave-one-out review of every rule'
status: Done
assignee: []
created_date: '2026-10-11 17:53'
updated_date: '2026-10-13 06:46'
labels:
  - epic
  - benchmark
dependencies: []
priority: high
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-11: remove each rule on its own and judge the effect; a rule whose removal improves the scores is a removal candidate. The usefulness check (TASK-11.15) dropped only the 30 most-firing rules, as probes of the datasets; this covers every rule that fires on any dataset, judged with the bench's verdicts (strict, within tolerance, rejected) on the full data and on dev/check. Caveat: a dataset cannot show what a rule protects that no dataset holds (a vendor token, German addresses), so a removal candidate needs a real-use note before it becomes a plugin change, which waits for the user's approval.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every rule that fired in the re-baselined run (TASK-19.7) has a judged disable mutation
- [x] #2 A ranked report under TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens): accepted removals by weighted FP/1k change, the floor or gap that rejects each other one, and the rules whose removal hurts most
- [x] #3 Removal candidates become plugin tasks with a real-use note, waiting for the user's approval
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:31
---
Paused 2026-10-11 (user): the move from gitleaks to Betterleaks (TASK-19) runs first, so leave-one-out runs once, on the new rule set. TASK-19.7 re-baselines and restarts it.
---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Leave-one-out done on the Betterleaks rule set: all 94 firing rules judged (TASK-18.1, loo run 20261012-200148 on baseline 20261012-194832), ranked under TASK-21.8's verdict by bench/rank.py (TASK-18.2, docs/BENCHMARK.md Leave-one-out). Removal candidates TASK-38 and TASK-39 wait for the user's approval in the inbox.
<!-- SECTION:FINAL_SUMMARY:END -->
