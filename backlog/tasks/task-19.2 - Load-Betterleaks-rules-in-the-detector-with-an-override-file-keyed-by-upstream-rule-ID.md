---
id: TASK-19.2
title: >-
  Load Betterleaks rules in the detector, with an override file keyed by
  upstream rule ID
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
labels:
  - detection
  - tdd
dependencies:
  - TASK-19.1
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
- [ ] #2 The per-rule fixes for vendored rules sit in the override file; a test fails when an override names a rule ID the vendored set lacks
- [ ] #3 Load time and first-scan time measured in the hook interpreter against today (463 rules against 222)
<!-- AC:END -->
