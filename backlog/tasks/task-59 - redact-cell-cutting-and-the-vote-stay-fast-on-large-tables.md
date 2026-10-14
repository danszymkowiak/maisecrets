---
id: TASK-59
title: 'redact: cell cutting and the vote stay fast on large tables'
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
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
- [ ] #1 within_cells and the overlap check in decide use bisect over sorted edges and starts
- [ ] #2 A synthetic 50,000-row, 10-column CSV with fake models runs through run_file in under 10 s; the test records the time
<!-- AC:END -->
