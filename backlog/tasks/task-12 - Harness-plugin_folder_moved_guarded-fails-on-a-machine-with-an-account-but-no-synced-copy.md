---
id: TASK-12
title: >-
  Harness: plugin_folder_moved_guarded fails on a machine with an account but no
  synced copy
status: To Do
assignee: []
created_date: '2026-10-11 08:06'
labels:
  - harness
  - guard
dependencies: []
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-10-11 during TASK-4; fails on main too (Claude Code 2.1.296). harness/run.py writes guard.json {expect: synced, accounts:[<account from ~/.claude.json>]} when an account file exists. On a machine without a synced maisecrets copy, guard.expected() returns False (registered account, no synced folder, nothing recently trashed), so the guard answers {} and the Bash call runs: ran.txt exists and the deny text never reaches the model. CI has no account file and uses expect=always, so it passes there. Debug log: the client itself reports 'Plugin directory does not exist' and runs the call anyway (#97847 still open). Likely fix: the scenario simulates the synced root (roots[account] pointing at the plugin copy) or uses expect=always; confirm it is the harness and not a guard regression.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scenario passes on a dev machine with ~/.claude.json and no synced copy
- [ ] #2 Scenario still fails when the guard is removed (proof it can fail)
<!-- AC:END -->
