---
id: TASK-59
title: 'redact: cell cutting and the vote stay fast on large tables'
status: Done
assignee: []
created_date: '2026-10-14 07:16'
updated_date: '2026-10-14 08:09'
labels:
  - redact
dependencies: []
ordinal: 120000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14: within_cells scans all cell edges for every span (spans x cells), and review.decide checks every model span against every rule span; column_spans (TASK-50) makes rule spans grow with the row count. A 50k-row CSV or a 10k-entry password export would stall for minutes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 within_cells and the overlap check in decide use bisect over sorted edges and starts
- [x] #2 A synthetic 50,000-row, 10-column CSV with fake models runs through run_file in under 10 s; the test records the time
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-10-14 on this machine: the 50,000-row, 10-column CSV took over 300 s before; after: 8.9-9.5 s, of which maisecrets.detect.scan alone takes 4.8 s (TASK-63). The time limit of 10 s is thin while the plugin scan is that slow; the test prints the time.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
within_cells, Masked.back and decide's rule and ask overlap checks use bisect (pipeline.overlapping); decide keeps a running group end; header_type and _time_header are cached per header; plausible/doubtful only look up the cell for spans that could be a GUID or timestamp; to_csv quotes by regex. test_large.py: 50,000 rows x 10 columns through run_file, the time printed, under 10 s. Follow-up: TASK-63 (the plugin scan).
<!-- SECTION:FINAL_SUMMARY:END -->
