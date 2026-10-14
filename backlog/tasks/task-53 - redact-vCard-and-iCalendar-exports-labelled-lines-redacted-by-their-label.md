---
id: TASK-53
title: 'redact: vCard and iCalendar exports - labelled lines redacted by their label'
status: Done
assignee: []
created_date: '2026-10-14 06:51'
updated_date: '2026-10-14 07:42'
labels:
  - redact
dependencies: []
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A .vcf contact export (FN, N, TEL, EMAIL, ADR, BDAY, NOTE) and an .ics calendar (ORGANIZER, ATTENDEE, LOCATION, SUMMARY, DESCRIPTION, video links with passcodes). A labelled line is a deterministic hit of its type; free text (NOTE, SUMMARY, DESCRIPTION) goes to the rules and models. Line folding (RFC 6350, RFC 5545) is undone before extraction.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A synthetic .vcf comes out with every name, phone, email, address and birthday redacted
- [x] #2 A synthetic .ics comes out with organizer, attendees and location redacted, and a meeting passcode in a description caught
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
extract._cards: unfolds lines, each property value a position (card N, field TEL), CN/EMAIL/SENT-BY parameters too; photos, logos, sounds, keys left out. pipeline.card_spans: FN/N/CN NAME, TEL PHONE, EMAIL/ORGANIZER/ATTENDEE EMAIL, ADR/LOCATION ADDRESS, BDAY DOB; a passcode (?pwd=, Passcode: ...) in NOTE/SUMMARY/DESCRIPTION is SECRET. Tests: test_cards.py.
<!-- SECTION:FINAL_SUMMARY:END -->
