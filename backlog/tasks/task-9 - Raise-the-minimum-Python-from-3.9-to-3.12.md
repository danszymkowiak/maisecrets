---
id: TASK-9
title: Raise the minimum Python from 3.9 to 3.12
status: Done
assignee: []
created_date: '2026-10-11 07:56'
updated_date: '2026-10-11 09:29'
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
- [x] #1 The launcher, dispatch and skill scripts refuse a Python older than 3.12 and their messages say 3.12
- [x] #2 README and CLAUDE.md state 3.12; no mention of 3.9 as supported remains
- [x] #3 All checks in CLAUDE.md pass with /usr/bin/python3 (3.12)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Floor raised to 3.12: run.sh/run.cmd probes and messages, run.sh drops python3.9-3.11 candidates, dispatch.py mod-prompt exits 3 below 3.12, skill _detector.py and protection_status.py (probe, messages, PYTHONS list), SKILL.md, mod comment, README (Requirements says stock macOS 3.9 is too old), CLAUDE.md, TESTING.md; .gitlab-ci.yml unit_python39 job and its needs removed, GitHub ci.yml comment. Tests pin 3.12 (test_promises, test_skill, mod.test.ts); new PythonFloorTests for dispatch and the skill detector, shown red with the old floor. Checks: 1112 tests OK, replay 108/108, scan_tree, derived_counts, lint_plugin, ruff, claude plugin test (16 pass), harness failures 0. Historic notes (DIAGNOSTICS.md, sync_gitleaks.py tomllib comment, _run_tests_json.py) left as they are: they record past facts, not support.
<!-- SECTION:FINAL_SUMMARY:END -->
