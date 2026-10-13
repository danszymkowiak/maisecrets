---
id: TASK-44
title: >-
  Plugin: switch on the normaliser stages ansi, cr, invisible, gutter, entity,
  fullwidth, decode and unwrap
status: Done
assignee: []
created_date: '2026-10-13 09:58'
updated_date: '2026-10-13 10:33'
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
- [x] #1 detect.NORMALISE holds the eight stages; the tests that pinned 'off by default' now pin the shipped set
- [x] #2 The full checks pass, the harness included; a bench run with the shipped set confirms the judged gains
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.NORMALISE = ansi, cr, invisible, gutter, entity, fullwidth, decode, unwrap (escape off). Tests pin the shipped set (test_normalise, test_decode); the ChatGPT skill zip now packs normalise.py, decode.py and unwrap.py (test_skill caught the missing import). Checks: 1,245 unit tests (the one failure was that zip, fixed), harness 0 failures, mod tests 16/16, 108/108 beliefs. Bench run 20261013-122613 against 20261013-120024: CredData +16 and Nemotron +4 finds, +2 false positives, SECRET_PREFIXED 1,634 -> 1,648 of 2,045. README (limits) and THREAT-MODEL C2 say what the scan now undoes and what not.
<!-- SECTION:FINAL_SUMMARY:END -->
