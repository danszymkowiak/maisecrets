---
id: TASK-1
title: Write design note docs/TERMS.md for personal term redaction
status: Done
assignee: []
created_date: '2026-10-11 07:00'
updated_date: '2026-10-11 07:11'
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
- [x] #1 Term file terms.txt in the maisecrets home folder, mode 0600, never read into a session; format 'LABEL  variant | variant | ...'
- [x] #2 Match modes: 'Jan' standalone (no letter/digit on either side), 'Kowalsk*' word start + any ending, '*kowalski' any start, '*kowalski*' anywhere
- [x] #3 Case-insensitive; whitespace inside a term matches any run of whitespace incl. line breaks; longest variant wins; the whole matched run is replaced
- [x] #4 Bare anywhere-terms (*x*) shorter than 4 characters rejected at load, error names the line number only
- [x] #5 PDF/image Read: 'ask' prompt; deny steers to pdftotext / tesseract-ocr (apt: tesseract-ocr tesseract-ocr-pol)
- [x] #6 Threat-model entry: what the control covers and where it ends (Read of PDF approved = no redaction; outputs >50K chars)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
docs/TERMS.md records the design: terms.txt (0600, home folder, under C8), the four * modes, matching rules, load errors by line number, stable placeholder per entity (key LABEL_c0: the grammar needs _cN, the vault mints from c1), resolve to the first plain variant under C4/C7/C9/C16, term rules after shape rules in detect.rules(), the PDF/image ask (Codex deny, guidance via session-start context), and a draft C25 row. Decisions filled in beyond the agreed outline: c0 key, canonical variant, rule order, guidance channel. Found: a Write that shows a placeholder is resolved by the installed hook; the doc writes it after the write.
<!-- SECTION:FINAL_SUMMARY:END -->
