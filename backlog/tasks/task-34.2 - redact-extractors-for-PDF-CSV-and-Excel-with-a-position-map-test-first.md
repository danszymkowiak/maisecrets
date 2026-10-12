---
id: TASK-34.2
title: 'redact: extractors for PDF, CSV and Excel with a position map (test first)'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:27'
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
- [x] #1 Tests first per format: generated fixture -> expected text and position map; a scanned or empty PDF reports that no text was found instead of an empty output
- [x] #2 A column can be dropped by header name (CSV, Excel)
- [x] #3 Every dependency's licence is recorded in redact/README.md and is permissive
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
redact/maisecrets_redact/extract.py: extract(path, drop_columns) -> Document (text + positions). PDF with pypdf, page by page, a PDF without text raises NoText ('no text found', no OCR); CSV with the csv module (delimiter sniffed), tab-separated rows, each cell mapped to 'row r, column <header>'; Excel with openpyxl read-only and data_only (values, not formulas), every sheet, cells mapped to 'sheet S, row r, column <header>'; .txt/.md pass through ('file'); other types raise Unsupported naming the type. A column is dropped by its header name (case-insensitive) in CSV and Excel. Tests generate every fixture (a minimal text PDF written by hand, an openpyxl workbook with a formula). Licences in redact/README.md: pypdf BSD-3-Clause, openpyxl MIT, et-xmlfile MIT; PyMuPDF (AGPL) not taken.
<!-- SECTION:FINAL_SUMMARY:END -->
