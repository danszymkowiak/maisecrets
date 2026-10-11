---
id: TASK-20
title: >-
  Plugin: a Swiss region (AHV/AVS and UID with checksums, DE/FR/IT context
  words)
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
labels:
  - plugin
  - detection
  - tdd
dependencies:
  - TASK-11.33
  - TASK-11.37
references:
  - >-
    research_notes/Deterministic redaction detection
    ideas/pii_and_personal_terms.md
priority: high
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided with the user 2026-10-11: their highest-risk content is tax, financial and personal documents, Swiss among them. maisecrets has no Swiss rule: none of the 74 vendored Presidio recognizers is Swiss. `regions` defaults to ["auto"], which on a Swiss system locale already resolves to `ch` (maisecrets/regions.py), but `ch` selects no rules and maps to German labels only (REGION_LANGUAGE).

Own rules, as stdlib validators in the style of the ported German ones:
- AHV/AVS number (Sozialversicherungsnummer, numéro AVS): 756 + 9 digits + EAN-13 check digit, written 756.1234.5678.97 or without dots.
- Company UID: CHE-123.456.789 (optionally with MWST/TVA/IVA), mod-11 check digit.
- Context words in German, French and Italian (AHV, AVS, Sozialversicherungsnummer, numéro AVS, numero AVS, UID, MWST, TVA, IVA, Steuernummer, numéro fiscal…).
Swiss IBANs are covered by the IBAN rule and +41 numbers by the phone rule; confirm both with a test rather than adding rules. Research note V2 (pii_and_personal_terms.md) lists AHV.

Because both checksums are strong, decide on the bench whether the dotted AHV form needs a context word (the bare 13-digit form should). The user sets their own regions (for example ["ch", "us"]) through /maisecrets:settings; tests never touch the real store.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first: valid and invalid AHV and UID numbers in each written form, the check digits against published examples, and a 13-digit number that fails EAN-13 is not matched
- [ ] #2 Region ch selects the new rules and the de, fr and it label languages; the auto resolution of a Swiss locale is tested
- [ ] #3 Judged on the bench: the synthetic Swiss templates (TASK-11.37) for recall, Gretel (TASK-11.33), TAB and Nemotron-PII as precision guards
- [ ] #4 README lists the Swiss region; derived_counts.py and the full check list pass
<!-- AC:END -->
