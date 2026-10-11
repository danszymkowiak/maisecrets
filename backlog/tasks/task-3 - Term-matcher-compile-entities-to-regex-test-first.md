---
id: TASK-3
title: 'Term matcher: compile entities to regex (test first)'
status: Done
assignee: []
created_date: '2026-10-11 07:00'
updated_date: '2026-10-11 07:30'
labels:
  - terms
  - tdd
dependencies:
  - TASK-2
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Compile parsed entities into one case-insensitive Unicode regex; boundary = not touching a letter or digit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Standalone 'Jan' matches 'Jan', 'Jan,', '(Jan)', 'Jan's', line/cell start and end; not 'January', 'Janek', 'Dajan'
- [x] #2 'Kowalsk*' matches Kowalski, Kowalskiego, Kowalskiej as one run; '*kowalski*' matches inside jkowalski@example.com
- [x] #3 Case-insensitive incl. Polish letters; whitespace in a term matches spaces, tabs and line breaks
- [x] #4 Longest variant wins: 'Jan Kowalski' is one match, not two
- [x] #5 Regex metacharacters in a term are escaped
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
terms.Matcher / compile_entities(entities): one IGNORECASE alternation of all variants, sorted longest first, named groups map a match back to its entity. Boundary = no Unicode letter/digit ([^\W_]) on the bounded side; STARTS/ENDS/INSIDE extend over the adjoining letters and digits so the whole run is replaced; whitespace in a variant is \s+; words are re.escape'd. find(text) -> [(start, end, Entity)]. 10 tests in tests/test_term_match.py (e-mail case built from parts). Also corrected the test count in docs/TESTING.md (stale since TASK-2). All checks green; 3.9 via uv.
<!-- SECTION:FINAL_SUMMARY:END -->
