---
id: TASK-15
title: >-
  False alarm: the word 'secrets', a colon and an English word in a markdown
  table cell
status: To Do
assignee: []
created_date: '2026-10-11 11:06'
updated_date: '2026-10-11 11:27'
labels:
  - detection
  - false-positive
dependencies: []
priority: low
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
2026-10-11: scripts/scan_tree.py flagged docs/BENCHMARK.md (rule ds-keyword-colon) on a table cell that read: the word secrets, then a colon, then 'precision and recall'. A keyword followed by a colon and an English word, in prose. The cell was reworded. Add the case to tests/fp_corpus.py NO_HIT (§-split, as the corpus writes keywords) and fix the rule, or leave it to the benchmark (TASK-11) to weigh. Writing this task tripped the pre-commit scan twice with the original wording.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Case in tests/fp_corpus.py NO_HIT
- [ ] #2 Detector silent on it, or a recorded decision to keep it
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
More cases of the same rule (ds-keyword-colon), 2026-10-11: CredData category names 'Password' and 'Token', each followed by a colon and 'Credential', in bench/labels/creddata.toml. Written there with the colon as the TOML escape u003A.
<!-- SECTION:NOTES:END -->
