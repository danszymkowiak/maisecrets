---
id: TASK-14
title: Find the flaky unit test that failed one pre-push run
status: To Do
assignee: []
created_date: '2026-10-11 10:18'
updated_date: '2026-10-11 15:15'
labels:
  - tests
  - flaky
dependencies:
  - TASK-16
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Second sighting 2026-10-11 ~14:10: a 'git commit' of bench files failed in the pre-commit hook and passed on an identical retry (output not captured). Both failures were under load (a 16-process bench run had just finished).

2026-10-11: not reproduced in 7 full runs: 4 suites in parallel (220 s each, all OK) and 3 runs of .githooks/pre-commit in parallel with a 16-process bench run as load (all OK). The git-calling tests already strip GIT_* (test_skill, test_release_scripts), so the hook environment is not the cause. Hooks now save the test output to .git/maisecrets-<hook>-tests.log and print FAIL lines on failure; the next occurrence names the test. Waiting for it (inbox TASK-16).

2026-10-11: user chose to leave this open, waiting for a recurrence; the hook logs will name the test. Do not work it in a loop until a log shows a failure.
<!-- SECTION:NOTES:END -->
