---
id: TASK-34.7
title: 'redact: reversible mode (--reversible) with a vault for the placeholder map'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-13 21:28'
labels:
  - redact
dependencies:
  - TASK-34.6
  - TASK-17
parent_task_id: TASK-34
priority: medium
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Spec, deferred part: one tool, a --reversible flag off by default. The deterministic and model passes run first and are load-bearing (raw data never reaches the later processing); each value becomes a placeholder and a vault holds the placeholder -> value map; a restore command (redact --restore <file> --vault <vault>) puts the values back into text that comes back. The vault becomes the most sensitive file: encrypted at rest (reuse the plugin's encrypted-file or keychain backend where it fits), never next to the output by default, and the tool says where it is. HIPAA / GDPR caveat in docs/REDACT.md: for real patient data get a compliance review. Decide with the user before building which vault backend and where it lives (inbox).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first: redact --reversible then --restore gives the original text back; without the vault nothing can be restored
- [ ] #2 The vault is encrypted at rest and never written into the output directory by default
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Not needed: user decision 2026-10-13, no healthcare use case.
<!-- SECTION:FINAL_SUMMARY:END -->
