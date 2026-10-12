---
id: TASK-34.3
title: >-
  redact: deterministic pass with the plugin's rules and consistent placeholders
  (test first)
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:36'
labels:
  - redact
  - tdd
dependencies:
  - TASK-34.2
parent_task_id: TASK-34
priority: high
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Run maisecrets.detect.scan on the extracted text with a RuleSet built from explicit settings (--regions, label languages; default: the user's maisecrets config if present, else generic), plus the personal terms file when given (docs/TERMS.md). Replace each hit with a placeholder of its type (⟦IBAN_1⟧ style), the same value getting the same placeholder across one run (a file or a directory). Structured PII found here is redacted without a vote (the rules are near-perfect on it).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tests first: an IBAN, a card, an e-mail and a secret in each format come out as placeholders; the same value twice gets one placeholder
- [x] #2 Regions and the terms file are options; the run reads no store or vault of the plugin
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
redact/maisecrets_redact/rules.py: detector(regions, languages) builds a RuleSet from explicit settings (or from the person's config, read only) and returns a detector over detect.scan; registered as 'rules'. Placeholders gives one ⟦TYPE_n⟧ per distinct value and type across a run, with counts. cli.py now redacts a single file: extract (with --drop-column), the rules (--regions), render, <file>.redacted.txt next to it or in --out; never overwrites an existing output or the input; a missing checkout writes nothing; the summary prints counts, never values. Tests: a token, an IBAN, a card and an e-mail in txt, csv, xlsx and pdf all become placeholders; the same value keeps its placeholder; --regions ch finds an AHV number; a run leaves the plugin home untouched; the command writes next to the input and refuses to overwrite. docs/REDACT.md: Use. Note: the plugin's terms file applies (docs/TERMS.md); only the store and vault stay closed.
<!-- SECTION:FINAL_SUMMARY:END -->
