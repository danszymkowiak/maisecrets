---
id: TASK-45
title: >-
  Vault: set up the Claude Code sandbox read deny for ~/.maisecrets, and have
  status say whether it is on
status: In Progress
assignee: []
created_date: '2026-10-13 10:21'
updated_date: '2026-10-13 10:40'
labels:
  - vault
  - security
dependencies: []
priority: high
ordinal: 106000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-13 (strengthen the vault). C8 is text matching for Bash: a command that builds the store path at run time still reads it (THREAT-MODEL C8: 'a backstop, not a boundary'). The README recommends the Claude Code sandbox with a read deny for ~/.maisecrets as the strongest step today, and this machine's settings have no sandbox section at all. (1) Propose the exact settings change to the user and apply it only after their yes (their own ~/.claude/settings.json). (2) Plugin side, test first: /maisecrets:status and the session primer report whether a sandbox deny covering the vault home is configured (user, project and managed settings), so a missing one is visible. (3) Measure in a real session that an obfuscated read of the store is refused with the sandbox on (a unit test cannot show what the sandbox allows; CLAUDE.md, Known traps).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The user's settings carry the sandbox read deny for the vault home, after their approval
- [x] #2 status reports the sandbox deny as present or missing; tests cover both and the settings layers
- [ ] #3 A real session shows a run-time-built read of the store refused under the sandbox; recorded in THREAT-MODEL C8
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-13: maisecrets/sandbox_check.py reads the Claude Code settings layers (project, project local, user via CLAUDE_CONFIG_DIR or ~/.claude, managed per OS; a later layer wins for enabled and filesystem.disabled, deny entries of every layer count) and says whether sandbox.credentials.files (mode deny) or sandbox.filesystem.denyRead covers the vault home; /maisecrets:status prints it (tests/test_sandbox_check.py). Schema read from the installed client 2.1.296. The settings change was proposed to the user in chat (sandbox.enabled true, credentials.files ~/.maisecrets deny, allowUnsandboxedCommands left default); waiting for their yes. Slip: while checking the line I ran the status command once against the real store (read, plus the routine expire sweep of Vault().list()); told the user.
<!-- SECTION:NOTES:END -->
