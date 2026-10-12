---
id: TASK-11.36
title: 'Bench: Kaggle PII Data Detection as a real-text check'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-12 09:27'
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
- [ ] #1 The competition terms are recorded; the adapter is opt-in (off by default) and needs the user's own Kaggle account and acceptance of the terms
- [ ] #2 An adapter and label table; the dataset is a guard (no weight in the mean) unless the usefulness check shows it adds information
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: blocked on the user's Kaggle account and acceptance of the competition terms (inbox TASK-17). No work started.
<!-- SECTION:NOTES:END -->
