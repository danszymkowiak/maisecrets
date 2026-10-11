---
id: TASK-6
title: 'PDF and image Read: ask prompt with pdftotext / OCR route on deny'
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
labels:
  - pdf
  - hooks
  - tdd
dependencies:
  - TASK-1
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PreToolUse on Read of .pdf/.png/.jpg/.jpeg/.gif/.webp/.tif/.tiff returns permissionDecision 'ask' (existing helper near maisecrets/hooks.py:1963), which also prompts in auto mode.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first: Read of a .pdf or image yields 'ask'; other files unchanged
- [ ] #2 Prompt text says approving sends the file unredacted, denying lets Claude extract text locally
- [ ] #3 Model-facing guidance names pdftotext -layout file.pdf - and tesseract image - -l pol+eng, whose output passes the redactor
- [ ] #4 Case-insensitive extensions (.PDF)
<!-- AC:END -->
