---
id: TASK-63
title: 'detect: scan time on a 2 MB table - 4.8 s of redact''s 9 s on 50,000 rows'
status: To Do
assignee: []
created_date: '2026-10-14 08:05'
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
- [ ] #1 A measurement names the rules that carry scan time on a 2 MB CSV-like text
- [ ] #2 Any speed-up keeps the bench verdict (no floor or guard worse)
<!-- AC:END -->
