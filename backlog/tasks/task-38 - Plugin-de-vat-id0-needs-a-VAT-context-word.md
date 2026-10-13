---
id: TASK-38
title: 'Plugin: de-vat-id#0 needs a VAT context word'
status: Done
assignee: []
created_date: '2026-10-12 19:32'
updated_date: '2026-10-13 20:11'
labels:
  - plugin
dependencies: []
priority: low
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-18.2 (leave-one-out): the bare form DE + 9 digits raised 60 false alarms on Gretel and no labelled find; its hits are FIX and XML identifiers that pass the checksum (49=SenderCompID, PartyID, ReportingBankID). Real use: a German VAT ID (USt-IdNr.) on an invoice, often a sole trader's, which nearly always stands next to USt-IdNr, VAT or Umsatzsteuer; the separated form (#1) is unchanged. Judged: bench/mutations/round5/de-vat-id-context.toml accepted against 20261012-194832 (weighted FP/1k -0.002). Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 de-vat-id#0 requires a context word; a test with and without one
- [x] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Applied in 809a0a9. Unit tests, replay_can_fail, scan, counts, lint, ruff green. Bench unit tests: 3 setUpClass errors under the Claude Code sandbox only (the forkserver of Python 3.14 needs a Unix socket, which the sandbox denies); to rerun outside it.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Applied in 809a0a9; unit tests, replay_can_fail and the bench tests pass (the bench pool fix in the next commit let them run in the sandbox). Judged on the bench in round5.
<!-- SECTION:FINAL_SUMMARY:END -->
