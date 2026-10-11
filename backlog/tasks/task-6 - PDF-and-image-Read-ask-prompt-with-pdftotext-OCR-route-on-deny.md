---
id: TASK-6
title: 'PDF and image Read: ask prompt with pdftotext / OCR route on deny'
status: Done
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-11 08:37'
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
- [x] #1 Tests first: Read of a .pdf or image yields 'ask'; other files unchanged
- [x] #2 Prompt text says approving sends the file unredacted, denying lets Claude extract text locally
- [x] #3 Model-facing guidance names pdftotext -layout file.pdf - and tesseract image - -l pol+eng, whose output passes the redactor
- [x] #4 Case-insensitive extensions (.PDF)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
PreToolUse on Read of .pdf/.png/.jpg/.jpeg/.gif/.webp/.tif/.tiff (any case) answers 'ask' in Claude Code with a reason that says approve sends the file unredacted and deny lets the agent extract its text locally; Codex gets a deny naming pdftotext/tesseract. The session-start PRIMER names pdftotext -layout file.pdf - and tesseract image.png - -l pol+eng. Store-path refusal still runs first; other files unchanged. tests/test_document_read.py (6 tests). Checks: 1102 tests OK, replay 103/103, scan_tree, derived_counts, lint_plugin, ruff green; harness unchanged (only plugin_folder_moved_guarded, TASK-12). Not measured: the real client's prompt for this ask (no harness scenario; claude -p refuses every ask).
<!-- SECTION:FINAL_SUMMARY:END -->
