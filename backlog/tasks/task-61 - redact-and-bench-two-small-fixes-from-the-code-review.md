---
id: TASK-61
title: 'redact and bench: two small fixes from the code review'
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
labels:
  - redact
dependencies: []
ordinal: 122000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14. (1) redact/tests/test_pipeline.py: CellTests and PlausibleTests come after the if __name__ == '__main__' guard, so running the file directly skips them. (2) bench/maisecrets_bench/run.py: a mutation run with MAISECRETS_BENCH_DETECTOR on an older checkout calls default_ruleset() and fails with an AttributeError inside the process pool instead of a clear BenchError; floors.py:61 repeats the known-type check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The main guard is the last statement of test_pipeline.py
- [ ] #2 A mutation run against an older detector stops at once with a BenchError naming MAISECRETS_BENCH_DETECTOR, with a test
- [ ] #3 floors.py:61 is simplified without a change in its output
<!-- AC:END -->
