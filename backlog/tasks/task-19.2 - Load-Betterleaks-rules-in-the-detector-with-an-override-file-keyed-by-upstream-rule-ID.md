---
id: TASK-19.2
title: >-
  Load Betterleaks rules in the detector, with an override file keyed by
  upstream rule ID
status: Done
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 10:18'
labels:
  - detection
  - tdd
dependencies:
  - TASK-21.8
parent_task_id: TASK-19
priority: high
ordinal: 55000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A loader for the converted Betterleaks rules next to _load_gitleaks (maisecrets/detect.py:471), behind a switch so the bench can compare both. tokenRatio has no stdlib equivalent: until TASK-19.3 decides, a rule that uses it falls back to its entropy limit (or is marked, so the bench can treat it separately).

Kingfisher's overlay pattern (crates/kingfisher-rules/data/imported-rules-capabilities.yml): our own fixes to a vendored rule live in one file keyed by the upstream rule ID, and the sync or a test fails when an ID there no longer exists upstream. Today these fixes are inline in detect.py (around 1182-1213) for generic-api-key, curl-auth-user, aws-access-token and hashicorp-tf-password; all four IDs exist in Betterleaks v1.9.0. Moving them makes false-positive fixes survive a rule sync instead of going quietly stale.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With the switch on, the detector loads Betterleaks rules; with it off, nothing changes (existing tests pass in both modes)
- [x] #2 The per-rule fixes for vendored rules sit in the override file; a test fails when an override names a rule ID the vendored set lacks
- [x] #3 Load time and first-scan time measured in the hook interpreter against today (463 rules against 222)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12 run: done and committed: maisecrets/filterexpr.py (evaluator, tokenRatio UNKNOWN, a failing filter keeps the hit), detect.SECRET_RULES switch ('gitleaks' default, 'betterleaks'), _load_betterleaks (global filter OR rule filter; skipReport and path-only rules left out; components do not gate), rules/overrides.txt + FIXES + override_problems(), the four inline fixes moved there, SigV4 belief retargeted, skill zip carries filterexpr.py. tests/test_betterleaks_rules.py. Full suite green in gitleaks mode. Open: AC #1 in Betterleaks mode (about 40 in-process tests fail, mostly generic-password and generic-credential-uri: inbox question), AC #3 timings not measured yet. A faulty scratch runner (rules loaded before tests/_isolate) bound the vault to the real home: see the inbox incident; never run the suite with detect imported before _isolate.

2026-10-12: user agreed to switch generic-password and generic-credential-uri off until TASK-19.3 benches them.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Done earlier (b5b2cbd): filterexpr.py, the SECRET_RULES switch (now Settings.secret_rules, TASK-27), _load_betterleaks, rules/overrides.txt with the four moved fixes. Now: overrides.txt takes 'off' (alone on its line; override_problems refuses it mixed with fixes), and generic-password and generic-credential-uri are off by the user's decision of 2026-10-12. AC #1 NOT fully met: with Betterleaks on (an isolated in-process run, tests/_isolate first) 1196 tests give 4 failures: 1 expected (test_ruleset checks that the default is gitleaks) and 3 recall differences: Betterleaks' generic-api-key has no password keyword (Betterleaks moved password labels into generic-password, which is off), so 'password: <value>' after another label on the line, or after a blank line, is missed. Handed to TASK-19.3 (generic-password on with its false positives, or a password keyword for generic-api-key) and TASK-19.4 (switch only when the suite passes). With the switch off nothing changes (the full suite passes). AC #3, /usr/bin/python3, median of 15: gitleaks 269 rules, load 3.9 ms, first scan 27.4 ms; Betterleaks 465 rules, load 7.9 ms, first scan 27.5 ms.
<!-- SECTION:FINAL_SUMMARY:END -->
