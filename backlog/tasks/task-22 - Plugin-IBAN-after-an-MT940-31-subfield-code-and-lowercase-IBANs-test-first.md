---
id: TASK-22
title: >-
  Plugin: IBAN after an MT940 ?31 subfield code, and lowercase IBANs (test
  first)
status: Done
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-12 06:51'
labels:
  - plugin
  - detection
  - tdd
dependencies:
  - TASK-21.8
priority: high
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Plugin, test first. Measured 2026-10-11 with the detector on synthetic text (the public example IBAN DE89 3704 0044 0532 0130 00): found plain, spaced, CSV, camt.053 <IBAN>, MT940 :25: and MT103 :59:/; missed MT940 :86: "?31DE89..." and lowercase "de89...".

German MT940 statements (and, as far as known, many Swiss banks' MT940 exports) put the counterparty IBAN in the :86: subfield ?31 (?30 BIC, ?32/?33 name). The IBAN rule's boundary sees the digits "31" right before the country code and rejects it, so every counterparty IBAN in a bank statement export reaches the model. Allow a ?NN subfield code (and a preceding "/") as a left boundary, and accept lowercase IBANs. Both stay gated by mod-97 and the country length, so the false-positive risk stays negligible. Gretel's "glued letter after" misses (...3000N) are generator artefacts and are not targeted.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tests first: ?31, ?30/?32 neighbours and /IBAN forms found; lowercase found; a mod-97 failure in each form not found
- [x] #2 Judged on the bench: Gretel structured group (TASK-11.33) for recall, precision unchanged on every dataset
- [x] #3 The synthetic tax templates (TASK-11.37) include MT940 :86: subfields
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The vendored Presidio IBAN pattern gets a left boundary that also takes an MT940 subfield code (?NN), patched at load (_presidio_regex). Lowercase IBANs are an own rule, iban-lowercase (plain or in groups of four, also after ?NN); _iban_ok holds a value with lowercase letters to its country's length (IBAN_LENGTH, SWIFT registry), since a lowercase hex digest passes mod 97 one time in 97. A first version made the vendored pattern case-insensitive: its optional groups then took the next word ('ES06... appar') and Gretel lost 2 IBANs, CredData 2 hits; split into two rules, the bench (run 20261012-084443 against 20261012-081433) finds the 594 findocs ?31 IBANs and nothing else moves. findocs' MT940 template already had :86: subfields (TASK-11.37). Found on the way: a hyphenated IBAN is never found (TASK-29).
<!-- SECTION:FINAL_SUMMARY:END -->
