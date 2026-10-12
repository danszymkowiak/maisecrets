---
id: TASK-34.2
title: 'redact: extractors for PDF, CSV and Excel with a position map (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - redact
  - tdd
dependencies:
  - TASK-34.1
parent_task_id: TASK-34
priority: high
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
One module per format, each returning flattened text plus a map from text offsets back to the source (PDF page; CSV row and column; Excel sheet, row and column) so a review can say where a span is. PDF: digital text only (no OCR), with pdfplumber (MIT) or pypdf (BSD); not PyMuPDF (AGPL) in a public Apache-2.0 repository. CSV: csv module, cell by cell, with an option to drop whole columns by header. Excel: openpyxl (MIT), values not formulas, every sheet. Plain .txt and .md pass through. Fixtures are generated in the tests (synthetic values only).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first per format: generated fixture -> expected text and position map; a scanned or empty PDF reports that no text was found instead of an empty output
- [ ] #2 A column can be dropped by header name (CSV, Excel)
- [ ] #3 Every dependency's licence is recorded in redact/README.md and is permissive
<!-- AC:END -->
