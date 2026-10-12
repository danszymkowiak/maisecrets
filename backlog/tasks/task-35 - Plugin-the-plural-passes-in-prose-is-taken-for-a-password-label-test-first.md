---
id: TASK-35
title: >-
  Plugin: the plural 'passes:' in prose is taken for a password label (test
  first)
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 16:13'
labels:
  - detection
  - false-positive
  - tdd
dependencies: []
priority: low
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-12 by the pre-commit scan on a task text: the words 'Combine the passes' followed by a colon and an ordinary word gave a ds-keyword-colon hit with that word as the value. 'passes' is a plural noun, not a credential label. Check which label matches (the denylist or a label file) and whether a whole-word rule for 'pass' fixes it without losing 'pass:', 'passwd:' or 'passphrase:'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test first: 'the passes: <word>' in prose is no hit; 'pass: <value>' still is
- [x] #2 Judged on the bench: no floor broken, false positives not higher
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fix merged (d1ab5a9, 9dae6fa): the en.txt pass label excludes passes, passed, passing, passive, passage, passenger. AC 2: judged by bench/mutations/round4/current-code.toml (no-op: the code against baseline 20261012-141549), queued.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
en.txt's pass label no longer takes passes, passed, passing, passive or passenger (passage stays: French clé de passage). Bench: the code against baseline 20261012-141549 accepted (mutation run of mutate-r6), FP down on ai4privacy, CredData and Gretel, no find lost.
<!-- SECTION:FINAL_SUMMARY:END -->
