---
id: TASK-9
title: Raise the minimum Python from 3.9 to 3.12
status: To Do
assignee: []
created_date: '2026-10-11 07:56'
labels:
  - tooling
dependencies: []
priority: low
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The fork runs only on this machine (system python3 is 3.12). Drop the 3.9 floor everywhere it is stated or checked: hooks/run.sh and run.cmd probes and messages, dispatch.py, skills/secret-hygiene scripts (_detector.py, protection_status.py), README, CLAUDE.md, tests that pin the 3.9 text (test_promises.py, test_skill.py). Keep the setup otherwise as it is; no uv, no new dependencies.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The launcher, dispatch and skill scripts refuse a Python older than 3.12 and their messages say 3.12
- [ ] #2 README and CLAUDE.md state 3.12; no mention of 3.9 as supported remains
- [ ] #3 All checks in CLAUDE.md pass with /usr/bin/python3 (3.12)
<!-- AC:END -->
