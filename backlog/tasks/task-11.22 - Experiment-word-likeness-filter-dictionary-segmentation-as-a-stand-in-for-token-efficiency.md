---
id: TASK-11.22
title: >-
  Experiment: word-likeness filter (dictionary segmentation) as a stand-in for
  token efficiency
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-12 21:29'
labels:
  - benchmark
dependencies:
  - TASK-11.18
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 4, the best-evidenced precision idea: Betterleaks reports F1 0.874 for token efficiency plus a word filter against 0.325 for entropy on CredData candidates (one author's benchmark, not verified). Stdlib surrogate: a bundled 10-30k word list and greedy segmentation of the value (camelCase, snake_case, kebab split first); the share of characters covered by words, or characters per segment, is the score. Compare against a character-bigram log-odds table. Apply only to entropy-only and weak-label hits, never to prefix-shaped tokens; passphrases and password123 are the known blind spot. The word list must carry a licence that allows a public repository; measure its load time and size.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A permissively licensed word list is chosen and its licence recorded; load time and memory measured in the hook's interpreter
- [ ] #2 Segmentation and bigram filters are mutations judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens), with Gretel and TAB in the FP objective
- [ ] #3 The report's 0.325 to 0.874 claim is restated with this bench's own numbers, whichever way they fall
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12, tooling in 97b5373: maisecrets_bench/wordlike.py (coverage by greedy segmentation, letter-bigram log-odds), filters bench:wordlike_75, bench:wordlike_44, bench:bigram_309 (skip outside a strong label), mutations bench/mutations/round3/{wordlike-75,wordlike-44,bigram-309}.toml. Word list: SCOWL american-english from the system (Debian wamerican 2020.12.07, SCOWL's permissive licence), not bundled; 73,133 words, 93 ms load, about 8 MB in /usr/bin/python3 3.12. Provisional judge under the OLD verdict (round 20261012-000333, baseline 20261011-220740, guard tab): wordlike-75 accepted within tolerance (dev +0.17, check +0.40, CredData +0.49); wordlike-44 rejected (dev +0.75, CredData +2.25, but ai4privacy -0.01 and recall -0.03 on ai4privacy/CredData); bigram-309 rejected (+0.01 / -0.01). Re-judge under TASK-21.8 on the new rule set.

2026-10-12 (TASK-21.10): wordlike-75, the mutation this experiment produced, is REJECTED under the floor verdict against 20261012-194832 (SECRET_GENERIC: one find lost on CredData). It was accepted within tolerance on 2026-10-11. A threshold that keeps every find, or none, before any plugin task.

2026-10-12 late: a judge of wordlike-44, bigram-309, label-weak-entropy (with label-negative and wordlike-75) against 20261012-194832 was started and stopped when the user paused; rerun: uv run --project bench python bench/mutate.py bench/mutations/round3/{wordlike-44,bigram-309,label-weak-entropy,label-negative,wordlike-75}.toml --baseline ~/.cache/maisecrets-bench/runs/20261012-194832. Known so far (TASK-21.10): label-negative accepted, wordlike-75 rejected.
<!-- SECTION:NOTES:END -->
