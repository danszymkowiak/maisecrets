---
id: TASK-7
title: Docs and full check suite for the fork
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-11 07:11'
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
- [ ] #1 README fork section: how to write terms.txt (synthetic example), chmod 600, the * modes, the PDF prompt
- [ ] #2 All checks in CLAUDE.md 'Checks before a push' pass, incl. /usr/bin/python3 3.9 and harness/run.py
- [ ] #3 Pushed to origin only after the user approves
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-1: move the draft C25 row from docs/TERMS.md into docs/THREAT-MODEL.md once its code and belief exist, and add C25 to the list in tests/test_beliefs_well_formed.py. docs/TERMS.md is developer-only in tests/test_release_tree.py; decide whether it ships.
<!-- SECTION:NOTES:END -->
