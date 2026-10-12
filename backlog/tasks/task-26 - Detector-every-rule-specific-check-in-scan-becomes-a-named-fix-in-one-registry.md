---
id: TASK-26
title: >-
  Detector: every rule-specific check in scan() becomes a named fix in one
  registry
status: Done
assignee: []
created_date: '2026-10-12 05:42'
updated_date: '2026-10-12 08:48'
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
- [x] #1 scan() has no rule-ID branch left; every check is a FIXES entry and each rule's fixes come from its loader or overrides.txt
- [x] #2 The full suite, the beliefs (scripts/replay_can_fail.py, anchors retargeted) and the bench baseline give the same results before and after
- [x] #3 The bench can disable one fix by name (a mutation kind), with a test
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
scan() keeps no rule-ID branch: every rule-specific drop check is a named entry of detect.FIXES (code-value, names-its-label, prose-in-table-cell, label-on-next-line, measure-number, uuid-elided-or-derived, user-as-password, template-braces, words-not-token, url-password-reference, phone-implausible, plus the vendored-rule fixes), and each rule lists its fixes: the detect-secrets loader (DS_KEYWORD_FIXES; user-as-password for ds-basic-auth), OWN_RULES ('fixes' key), rules/overrides.txt for vendored rules. The YAML anchor step is a rule field (value_after_anchor). Type-wide checks (placeholder, repeated character, token extension, IP section number) stay in scan(). Bench: op = 'unfix' switches one fix off by name, for one rule or every rule (tests in bench/tests/test_mutation.py). Same results: unit suite 1187 OK, 108/108 beliefs, bench detections identical to run 20261012-102454 (503,733 of 503,733, run 20261012-104218).
<!-- SECTION:FINAL_SUMMARY:END -->
