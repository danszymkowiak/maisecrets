---
id: TASK-1
title: Write design note docs/TERMS.md for personal term redaction
status: To Do
assignee: []
created_date: '2026-10-11 07:00'
labels:
  - design
  - terms
dependencies: []
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Record the agreed design: a per-person term file, per-variant match modes with *, stable entity placeholders, a PDF/image read prompt. Fork-only feature; upstream README says names are not detected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Term file terms.txt in the maisecrets home folder, mode 0600, never read into a session; format 'LABEL  variant | variant | ...'
- [ ] #2 Match modes: 'Jan' standalone (no letter/digit on either side), 'Kowalsk*' word start + any ending, '*kowalski' any start, '*kowalski*' anywhere
- [ ] #3 Case-insensitive; whitespace inside a term matches any run of whitespace incl. line breaks; longest variant wins; the whole matched run is replaced
- [ ] #4 Bare anywhere-terms (*x*) shorter than 4 characters rejected at load, error names the line number only
- [ ] #5 PDF/image Read: 'ask' prompt; deny steers to pdftotext / tesseract-ocr (apt: tesseract-ocr tesseract-ocr-pol)
- [ ] #6 Threat-model entry: what the control covers and where it ends (Read of PDF approved = no redaction; outputs >50K chars)
<!-- AC:END -->
