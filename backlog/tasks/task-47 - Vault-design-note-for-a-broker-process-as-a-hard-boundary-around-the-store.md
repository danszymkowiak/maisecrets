---
id: TASK-47
title: 'Vault: design note for a broker process as a hard boundary around the store'
status: Done
assignee: []
created_date: '2026-10-13 10:21'
updated_date: '2026-10-13 21:28'
labels:
  - vault
  - security
  - design
dependencies: []
priority: low
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-13. The threat model says C8 is a backstop and 'a hard boundary needs a broker process'. Write docs/BROKER.md: what runs where (a separate user, a system service, or an OS-level sandbox profile), how hooks ask for a value (socket, peer credentials), how the gates C4, C5, C7, C9 move into the broker, what it costs to install on macOS, Windows and Linux, and what it still does not stop (A3 with the person's rights, A5). No code: the note is for the user to decide whether to build it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 docs/BROKER.md covers placement, protocol, gates, install cost per OS and the remaining gaps
- [x] #2 An inbox question asks the user whether to build it
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Not built: user decision 2026-10-13 (no). The design note stays in docs/BROKER.md.
<!-- SECTION:FINAL_SUMMARY:END -->
