---
id: TASK-63
title: 'detect: scan time on a 2 MB table - 4.8 s of redact''s 9 s on 50,000 rows'
status: Done
assignee: []
created_date: '2026-10-14 08:05'
updated_date: '2026-10-14 08:47'
labels:
  - detect
  - perf
dependencies: []
ordinal: 124000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found in TASK-59 (2026-10-14): on a synthetic 50,000-row, 10-column CSV (1.9 MB of text) redact's own steps take about 4 s after the bisect fixes, and maisecrets.detect.scan takes 4.8 s of the remaining 9 s (cProfile: _matches, 39 calls). The plugin scans tool output of that size too, so the cost matters there as well. Measure scan per rule on large structured text and see whether a few rules carry the time; any change goes through the bench (docs/BENCHMARK.md) like every rule change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A measurement names the rules that carry scan time on a 2 MB CSV-like text
- [x] #2 Any speed-up keeps the bench verdict (no floor or guard worse)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-10-14, per rule on two 50,000-row tables. (1) 4.3 MB with an e-mail, date, amount and IBAN-like value per row: full scan 70 s, the email rule alone 84 s as a single rule; cause: the normaliser's second pass (the gutter stage strips the row numbers, so the copy differs) looked up the raw hits a copy hit overlaps by scanning all of them, quadratic in the hits. Fixed with bisect over the taken spans: 9.8 s. (2) 2.2 MB of Name/testpass rows: 5.3 s before and after; six ds-keyword-* line rules take about 0.6 s each because 'pass' is on every line; linear, left as is. scan() output identical before and after on 21,000 bench texts (7 datasets x 3,000, 36,017 hits, same hash), so the bench verdict cannot change.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.scan keeps its matches in start order next to taken_starts; the normaliser pass finds the hits a copy hit overlaps by bisect instead of a scan over all hits. A 50,000-address table: 70 s -> 9.8 s. Output identical on 21,000 bench texts. Regression test: tests/test_normalise.py LargeTextTests. docs/TESTING.md count 1269.
<!-- SECTION:FINAL_SUMMARY:END -->
