---
id: TASK-14
title: Find the flaky unit test that failed one pre-push run
status: To Do
assignee: []
created_date: '2026-10-11 10:18'
labels:
  - tests
  - flaky
dependencies: []
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
2026-10-11: the first git push failed at 'pre-push: unit tests failed'; the same suite passed right before (standalone, 1112 OK) and in the next push. The failing test was not captured. Run the suite several times in the pre-push environment (git sets GIT_DIR etc. for hooks; load from parallel commits), capture the FAIL lines, fix the test or its timing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The flaky test is named, with its failure output
- [ ] #2 Fixed, and 5 consecutive suite runs pass
<!-- AC:END -->
