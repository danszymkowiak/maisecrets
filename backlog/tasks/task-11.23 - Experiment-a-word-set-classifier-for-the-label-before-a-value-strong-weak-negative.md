---
id: TASK-11.23
title: >-
  Experiment: a word-set classifier for the label before a value (strong, weak,
  negative)
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
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 3. Split the identifier before a value into words (camelCase, snake_case, kebab, dots) and classify by word sets, as Bandit and CodeQL do: strong (api+key, client+secret, password, token as the last word) allows a low-entropy value; weak (key, auth, credential) needs entropy or a shape; a negative sibling (count, max, hash, path, url, id, length, file, name, type, tokenizer, secretary, passwordless) blocks. This would replace part of the growing stack of label exceptions in detect.py. Implement as a bench filter on the keyword rules (ds-keyword-*, generic-api-key); list which existing exceptions it subsumes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The word sets live in one table; a unit test covers each listed negative sibling
- [ ] #2 Judged on dev and check; false alarms removed and finds lost per rule reported
- [ ] #3 A list of the detect.py label special cases the classifier makes redundant, if it passes
<!-- AC:END -->
