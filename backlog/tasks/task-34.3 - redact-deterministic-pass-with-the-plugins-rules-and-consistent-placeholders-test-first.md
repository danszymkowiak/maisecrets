---
id: TASK-34.3
title: >-
  redact: deterministic pass with the plugin's rules and consistent placeholders
  (test first)
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
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
- [ ] #1 Tests first: an IBAN, a card, an e-mail and a secret in each format come out as placeholders; the same value twice gets one placeholder
- [ ] #2 Regions and the terms file are options; the run reads no store or vault of the plugin
<!-- AC:END -->
