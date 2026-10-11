---
id: TASK-7
title: Docs and full check suite for the fork
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-11 09:02'
labels:
  - docs
dependencies:
  - TASK-5
  - TASK-6
priority: medium
ordinal: 7000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README fork section: how to write terms.txt (synthetic example), chmod 600, the * modes, the PDF prompt
- [ ] #2 All checks in CLAUDE.md 'Checks before a push' pass, incl. /usr/bin/python3 3.9 and harness/run.py
- [ ] #3 Pushed to origin only after the user approves
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-1: move the draft C25 row from docs/TERMS.md into docs/THREAT-MODEL.md once its code and belief exist, and add C25 to the list in tests/test_beliefs_well_formed.py. docs/TERMS.md is developer-only in tests/test_release_tree.py; decide whether it ships.

2026-10-11: README 'Personal terms (this fork)' section (terms.txt example, chmod 600, * modes, placeholder, fail closed, PDF/image prompt, not caught) and a pointer from 'Names are not detected'. C25 row moved from docs/TERMS.md into docs/THREAT-MODEL.md; five beliefs beliefs/c25-*.toml (placeholder, never stored, bad file fails closed, no term in a message, document Read asks), C25 added to tests/test_beliefs_well_formed.py; README proofs 103 -> 108. Checks green: 1110 tests on 3.12 and on 3.9 (uv cpython-3.9, /usr/bin/python3 is 3.12 here), replay 108/108, scan_tree, derived_counts, lint_plugin, ruff. OPEN: AC2 harness: only plugin_folder_moved_guarded fails, also on main (TASK-12). AC3: push waits for the user (inbox TASK-13). docs/TERMS.md stays developer-only (not in the release tree), as in tests/test_release_tree.py.
<!-- SECTION:NOTES:END -->
