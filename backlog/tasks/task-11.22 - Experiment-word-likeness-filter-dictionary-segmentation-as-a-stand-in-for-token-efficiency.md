---
id: TASK-11.22
title: >-
  Experiment: word-likeness filter (dictionary segmentation) as a stand-in for
  token efficiency
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.18
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 4, the best-evidenced precision idea: Betterleaks reports F1 0.874 for token efficiency plus a word filter against 0.325 for entropy on CredData candidates (one author's benchmark, not verified). Stdlib surrogate: a bundled 10-30k word list and greedy segmentation of the value (camelCase, snake_case, kebab split first); the share of characters covered by words, or characters per segment, is the score. Compare against a character-bigram log-odds table. Apply only to entropy-only and weak-label hits, never to prefix-shaped tokens; passphrases and password123 are the known blind spot. The word list must carry a licence that allows a public repository; measure its load time and size.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A permissively licensed word list is chosen and its licence recorded; load time and memory measured in the hook's interpreter
- [ ] #2 Segmentation and bigram filters are mutations judged on dev and check with Gretel and TAB as guards
- [ ] #3 The report's 0.325 to 0.874 claim is restated with this bench's own numbers, whichever way they fall
<!-- AC:END -->
