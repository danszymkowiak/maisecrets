---
id: TASK-44
title: >-
  Plugin: switch on the normaliser stages ansi, cr, invisible, gutter, entity,
  fullwidth, decode and unwrap
status: To Do
assignee: []
created_date: '2026-10-13 09:58'
labels:
  - plugin
dependencies: []
priority: medium
ordinal: 105000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Approved by the user 2026-10-13 (inbox TASK-17): detect.NORMALISE gets the six stages of TASK-11.25 plus decode (TASK-11.26) and unwrap with the cheaper guard (TASK-37). escape stays off. Docs (README, THREAT-MODEL where it describes the scan, BENCHMARK) say they are on.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detect.NORMALISE holds the eight stages; the tests that pinned 'off by default' now pin the shipped set
- [ ] #2 The full checks pass, the harness included; a bench run with the shipped set confirms the judged gains
<!-- AC:END -->
