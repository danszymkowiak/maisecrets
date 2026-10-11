---
id: TASK-11.36
title: 'Bench: Kaggle PII Data Detection as a real-text check'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
labels:
  - benchmark
  - dataset
dependencies: []
parent_task_id: TASK-11
priority: low
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Learning Agency Lab's Kaggle competition data: student essays, labelled by people (names, emails, usernames, ID numbers, phone numbers, URLs, addresses). Not financial, but real text, so it checks for artefacts that synthetic datasets hide. Download needs a Kaggle account and API token, which the user provides; the setup reads it from the environment or ~/.kaggle and never prints it. Personal, local use (user, 2026-10-11): a licence only needs to allow the user's own non-commercial measurement; the data still never enters the repository (docs/BENCHMARK.md, Hygiene) and a report that goes elsewhere leaves it out.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The competition licence is recorded and allows local personal use
- [ ] #2 An adapter and label table; the dataset is a guard (no weight in the mean) unless the usefulness check shows it adds information
<!-- AC:END -->
