---
id: TASK-46
title: >-
  Vault: on Linux keep the store's key out of the store directory (Secret
  Service, with the key file as fallback)
status: Done
assignee: []
created_date: '2026-10-13 10:21'
updated_date: '2026-10-13 21:18'
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
- [x] #1 With a Secret Service the key is not in the vault home; without one the key file works as today; tests for both and for the migration
- [x] #2 A real session on this machine and in the sandbox resolves a value with the new backend
- [x] #3 THREAT-MODEL C12 and README state what changed and what A3 still can
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built in ac8ce04: key_store file|secret-service (opt-in), secret-tool on stdin/stdout, openssl gets the key over a pipe fd, marker key.location, migration with read-back, fail closed (store.key-secret-service), wipe clears the item. 9 tests with a fake secret-tool; belief c12-a-moved-store-key-is-never-replaced. AC#2 open: secret-tool (libsecret-tools) is not installed on this machine, and a real run touches the user's keyring, which CLAUDE.md forbids without the user.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Built in ac8ce04 (opt-in key_store: secret-service; migration with read-back; fail closed with store.key-secret-service). Measured 2026-10-13 with the user's approval on the real keyring with a temp home and a synthetic value: outside the sandbox put/get in two processes, no key file, marker set; inside the sandbox the moved key fails closed and a new store falls back to the key file; wipe removed the keyring item (lookup rc 1). README updated.
<!-- SECTION:FINAL_SUMMARY:END -->
