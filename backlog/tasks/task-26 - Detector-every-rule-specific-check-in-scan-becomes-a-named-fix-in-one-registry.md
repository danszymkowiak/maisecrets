---
id: TASK-26
title: >-
  Detector: every rule-specific check in scan() becomes a named fix in one
  registry
status: To Do
assignee: []
created_date: '2026-10-12 05:42'
labels:
  - refactor
  - detection
dependencies: []
references:
  - maisecrets/detect.py
  - maisecrets/rules/overrides.txt
priority: medium
ordinal: 1100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
scan() carries about 20 branches of the form 'if rule.id == X (or startswith ds-keyword) and check: continue'. TASK-19.2 started a registry (detect.FIXES, keyed by name, attached to vendored rules through rules/overrides.txt). Extend it to the detect-secrets rules (ds-keyword-*, ds-basic-auth), the own rules (url-query-secret, auth-scheme, url-password-no-user, phone) and the type checks (IP section numbers), so each check has a name and a rule lists the fixes it takes.

Why: the bench can switch a fix on or off by name (leave-one-out, TASK-18), a new rule such as Betterleaks' generic-password reuses the detect-secrets fixes with one line (TASK-19.2/19.3), and the plugin tasks (TASK-11.28 to 11.32, TASK-22 to 24) add a named fix instead of another branch. Behaviour must not change: a pure refactor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 scan() has no rule-ID branch left; every check is a FIXES entry and each rule's fixes come from its loader or overrides.txt
- [ ] #2 The full suite, the beliefs (scripts/replay_can_fail.py, anchors retargeted) and the bench baseline give the same results before and after
- [ ] #3 The bench can disable one fix by name (a mutation kind), with a test
<!-- AC:END -->
