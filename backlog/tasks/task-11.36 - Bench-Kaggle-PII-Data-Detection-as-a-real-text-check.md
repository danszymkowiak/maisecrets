---
id: TASK-11.36
title: 'Bench: Kaggle PII Data Detection as a real-text check'
status: Done
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-13 21:28'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-17
parent_task_id: TASK-11
priority: low
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Learning Agency Lab's Kaggle competition data: student essays, labelled by people (names, emails, usernames, ID numbers, phone numbers, URLs, addresses). Not financial, but real text, so it checks for artefacts that synthetic datasets hide. Download needs a Kaggle account and API token, which the user provides; the setup reads it from the environment or ~/.kaggle and never prints it. The fork is public and anyone may run the bench (user, 2026-10-11), so the licence must hold for any user, not only the owner. A dataset whose terms restrict use (non-commercial, competition-only, no derivatives, an account to accept terms) is opt-in like ai4privacy: a setup flag, off by default, its terms named in bench/README.md, and the person running it accepts them. The data and anything derived from it never enter the repository (docs/BENCHMARK.md, Hygiene).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The competition terms are recorded; the adapter is opt-in (off by default) and needs the user's own Kaggle account and acceptance of the terms
- [x] #2 An adapter and label table; the dataset is a guard (no weight in the mean) unless the usefulness check shows it adds information
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: blocked on the user's Kaggle account and acceptance of the competition terms (inbox TASK-17). No work started.

2026-10-12: token present (.env, read only by the setup at run time); competition listed; download 403 until the rules are accepted (inbox). Building the opt-in adapter against the published format (train.json: document, full_text, tokens, trailing_whitespace, BIO labels) with a synthetic fixture.

Adapter built and committed (df89b9f): bench/maisecrets_bench/adapters/kagglepii.py, labels/kagglepii.toml, setup.py --with-kaggle-pii, guard and local-only in run.py, terms in bench/README.md; tests with made-up records. The real run waits on the inbox: accept the competition rules with your Kaggle account, and paste the data licence. Then: uv run --project bench python bench/setup.py --only kagglepii, and the usefulness check (AC 2).

2026-10-13: rules accepted by the user; downloaded (6,807 essays, 1,606 labelled spans, 45 in scope). Run 20261013-230908: TP 44, FP 3 in 4.1M tokens (0.001/1k; Gretel 0.7), recall 97.8%, out-of-scope labels touched 2 of 1,561. usefulness.py: keep. Kept as a guard: 45 in-scope values are too few for weight in the mean; its value is the real-text false-alarm rate. AC1 waits for the data licence text (the rules page renders in the browser only).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
PIILO (the competition data) is CC BY 4.0 (the-learning-agency-lab.com, user 2026-10-13): recorded with attribution, no longer local-only; still opt-in because the download needs the user's Kaggle account and the competition rules. Measured run 20261013-230908: 44/45 in scope, 3 FP in 4.1M tokens. Guard, not weighted (45 values). Commits df89b9f, 593033f and this one.
<!-- SECTION:FINAL_SUMMARY:END -->
