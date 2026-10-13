---
id: TASK-46
title: >-
  Vault: on Linux keep the store's key out of the store directory (Secret
  Service, with the key file as fallback)
status: To Do
assignee: []
created_date: '2026-10-13 10:21'
labels:
  - vault
  - security
dependencies: []
priority: medium
ordinal: 107000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-13. On Linux the encrypted store file and its key (~/.maisecrets/key, 0600) sit side by side, so a backup or a copy of the disk (A4) holds both. Test first: a backend option that keeps the key in the Secret Service (secret-tool / libsecret, gnome-keyring or KWallet) and falls back to the key file when no Secret Service runs (headless, CI, the Claude Code sandbox; check what the sandbox allows in a real session). Migration of an existing key without loss; a damaged or missing key is never replaced silently (C12). README: exclude ~/.maisecrets from backups either way. Does not help against A3 (a process of the same user): say so.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With a Secret Service the key is not in the vault home; without one the key file works as today; tests for both and for the migration
- [ ] #2 A real session on this machine and in the sandbox resolves a value with the new backend
- [ ] #3 THREAT-MODEL C12 and README state what changed and what A3 still can
<!-- AC:END -->
