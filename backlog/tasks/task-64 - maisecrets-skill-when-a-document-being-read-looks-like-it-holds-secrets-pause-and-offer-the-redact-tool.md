---
id: TASK-64
title: >-
  maisecrets skill: when a document being read looks like it holds secrets,
  pause and offer the redact tool
status: Done
assignee: []
created_date: '2026-10-14 09:03'
updated_date: '2026-10-14 09:19'
labels:
  - skill
  - redact
dependencies: []
ordinal: 125000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User, 2026-10-14: if Claude sees that a document it is about to read (or has started reading) holds secrets or personal data in bulk, such as a password manager or browser password export, it pauses and offers to run the redact tool on it first, then reads the redacted output. This avoids mistakes like reading a password export by accident, and gives the user a simple way to continue without redacting the file by hand. Skill text only: no models or new work in the plugin's hooks (models stay in redact). The offer names the command (redact <file>, output next to the file) and what happens without the redact tool installed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The maisecrets skill tells Claude when to pause: file names and headers of exports (logins.csv, passwords, .har, .vcf), or a first look that shows secrets in bulk
- [x] #2 The offer names the redact command for that file and its output, and Claude reads the output instead of the original once it exists
- [x] #3 When redact is not installed, the offer says how to install it (docs/REDACT.md, Install)
- [x] #4 A test or a harness scenario covers the skill text (lint_plugin passes; the wording is checked)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
secret-hygiene SKILL.md: the description now triggers when Claude is about to read a document that looks like it holds secrets in bulk; a new section 'Before you read a document full of secrets' names the signs (password exports, .har, .vcf/.ics, key files, header row, a first look), says to stop and offer a redacted copy, uses redact <file> when on PATH (outputs .redacted.csv/.txt, install pointer docs/REDACT.md) and scripts/redact_copy.py otherwise, then reads only the output; on a no it does not read the file. Tests: tests/test_skill.py ReadAnExportTests; lint_plugin passes.
<!-- SECTION:FINAL_SUMMARY:END -->
