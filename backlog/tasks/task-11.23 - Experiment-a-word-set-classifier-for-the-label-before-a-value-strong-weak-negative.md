---
id: TASK-11.23
title: >-
  Experiment: a word-set classifier for the label before a value (strong, weak,
  negative)
status: In Progress
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-13 06:47'
labels:
  - benchmark
dependencies:
  - TASK-11.18
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 3. Split the identifier before a value into words (camelCase, snake_case, kebab, dots) and classify by word sets, as Bandit and CodeQL do: strong (api+key, client+secret, password, token as the last word) allows a low-entropy value; weak (key, auth, credential) needs entropy or a shape; a negative sibling (count, max, hash, path, url, id, length, file, name, type, tokenizer, secretary, passwordless) blocks. This would replace part of the growing stack of label exceptions in detect.py. Implement as a bench filter on the keyword rules (ds-keyword-*, generic-api-key); list which existing exceptions it subsumes.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The word sets live in one table; a unit test covers each listed negative sibling
- [ ] #2 Judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens); FP per 1,000 tokens removed and finds lost reported per rule and type
- [ ] #3 A list of the detect.py label special cases the classifier makes redundant, if it passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12, tooling in 97b5373: maisecrets_bench/labelclass.py (one table: STRONG_LAST, STRONG_PAIRS, WEAK, NEGATIVE_LAST, NEGATIVE_WHOLE; passport, id and passage kept out of the negatives by dev evidence), filters bench:label_negative and bench:label_weak_entropy, mutations in bench/mutations/round3/. Provisional judge under the OLD verdict (round 20261012-000333): label-negative accepted strictly (dev +0.01, check +0.16, CredData +0.04); label-weak-entropy rejected (CredData recall 64.33% to 64.23%). Re-judge under TASK-21.8 on the new rule set.

2026-10-12 late: a judge of wordlike-44, bigram-309, label-weak-entropy (with label-negative and wordlike-75) against 20261012-194832 was started and stopped when the user paused; rerun: uv run --project bench python bench/mutate.py bench/mutations/round3/{wordlike-44,bigram-309,label-weak-entropy,label-negative,wordlike-75}.toml --baseline ~/.cache/maisecrets-bench/runs/20261012-194832. Known so far (TASK-21.10): label-negative accepted, wordlike-75 rejected.
<!-- SECTION:NOTES:END -->
