---
id: TASK-38
title: 'Plugin: de-vat-id#0 needs a VAT context word'
status: To Do
assignee: []
created_date: '2026-10-12 19:32'
updated_date: '2026-10-13 09:59'
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
- [ ] #1 de-vat-id#0 requires a context word; a test with and without one
- [ ] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->
