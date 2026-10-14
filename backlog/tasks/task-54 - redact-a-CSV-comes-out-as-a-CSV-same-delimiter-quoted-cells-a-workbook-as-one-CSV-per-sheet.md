---
id: TASK-54
title: >-
  redact: a CSV comes out as a CSV - same delimiter, quoted cells; a workbook as
  one CSV per sheet
status: To Do
assignee: []
created_date: '2026-10-14 06:56'
labels:
  - redact
dependencies: []
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Today every output is <file>.redacted.txt (TASK-34): a table becomes tab-separated text without quoting, so a cell holding a tab or a line break shifts its row's columns or splits the row. Since TASK-49 no span crosses a cell, so the tool can redact cell by cell and write rows back with the csv module (user, 2026-10-14). Do before TASK-51 so its tests check the real CSV output.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A .csv or .tsv comes out as <file>.redacted.csv with the input's delimiter and the header row; cells with a delimiter, quote, tab or line break are quoted and stay one cell
- [ ] #2 An .xlsx or .xlsm comes out as one <file>.<sheet>.redacted.csv per sheet; a sheet name unsafe in a file name is made safe
- [ ] #3 Dropped columns stay dropped; one value keeps one placeholder across the run
- [ ] #4 A directory run skips earlier outputs of every kind (*.redacted.txt and *.redacted.csv), and an existing output is never overwritten
- [ ] #5 docs/REDACT.md and redact/README.md describe the outputs
<!-- AC:END -->
