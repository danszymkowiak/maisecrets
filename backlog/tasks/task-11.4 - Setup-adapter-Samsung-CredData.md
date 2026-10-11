---
id: TASK-11.4
title: 'Setup adapter: Samsung CredData'
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 10:20'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.3
parent_task_id: TASK-11
priority: medium
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read ../CredData (path configurable): meta/*.csv (68,234 lines: T 15,753, F 48,061, X 4,082) and data/ files; one sample per labelled line (LineStart..LineEnd) with the value span (ValueStart/ValueEnd; -1 = whole line, negatives only); Category -> maisecrets type mapping; group = RepoName/FileID. Decide whether unlabelled lines of the files count as negatives (design note). Values are obfuscated but keep their shape: never print one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Row counts per label match the meta files
- [ ] #2 No value appears in logs or output (test)
<!-- AC:END -->
