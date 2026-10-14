---
id: TASK-49
title: >-
  redact: a city labelled EMAIL, and a name across two CSV cells merged into one
  placeholder
status: Done
assignee: []
created_date: '2026-10-14 05:52'
updated_date: '2026-10-14 06:21'
labels:
  - redact
dependencies: []
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-14 on a synthetic 120-row CSV (first,last,email,city) with the models on: 'Zurich' in the first rows got an EMAIL placeholder (some model's label maps to EMAIL, or a span crosses cells), and merge_pieces joins first and last name across the tab, so the row loses a column. Look at which model and label; a span must not cross a cell boundary of a table.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Which model and label gave the city EMAIL, with a test
- [x] #2 A span never crosses a CSV/Excel cell boundary; a test
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-10-14 with the four default models on a synthetic 120-row CSV: fastino/gliner2-privacy-filter-PII-multi gives the city its 'email' label (0.62 to 0.73) only when the email cell holds the rules' [EMAIL]; with the address in the text it finds the address, without an email column nothing. No span crossed a cell for that one, but privacy-filter and gliner2 answered first<TAB>last as one NAME, and gliner2 one EMAIL over five cells and a line break. Fix: pipeline.within_cells cuts every span (rules and models) at the document's position edges, pipeline.plausible drops a model EMAIL without an @. End to end: 121 of 121 rows keep their 4 columns. Left open: the vote still redacts 25 of 120 cities as NAME (gliner2 or knowledgator agreeing with privacy-filter), a model false positive, not this task.
<!-- SECTION:NOTES:END -->
