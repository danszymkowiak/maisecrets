---
id: TASK-19.1
title: Betterleaks sync script with a filter-expression converter (test first)
status: Done
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 05:03'
labels:
  - detection
  - tdd
dependencies:
  - TASK-21.8
references:
  - scripts/sync_gitleaks.py
  - >-
    https://github.com/betterleaks/betterleaks/blob/v1.9.0/config/betterleaks.toml
parent_task_id: TASK-19
priority: high
ordinal: 54000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
scripts/sync_betterleaks.py vX.Y.Z, modelled on sync_gitleaks.py: fetch config/betterleaks.toml and LICENSE at the tag, read them as data (nothing upstream runs), write betterleaks.toml, betterleaks.json, LICENSE-betterleaks and BETTERLEAKS_VERSION. Pin v1.9.0 (latest stable); move to v2.0.0 in a follow-up once it is final.

Rule filters are expressions (CEL in v1.9, Expr in v2). The functions in use are few (v2 counts): entropy (414), tokenRatio (124), matchesAny (98), containsAny (45), len (18), on finding["secret"] and similar fields, combined with || and &&. Convert that subset into data the detector reads; accept both the v1.9 names (filter.entropy) and the v2 names (entropy). The file-level filter (true/false/null, repeated characters, $VAR, ${VAR}, {{ }} templates) and prefilter (paths) convert the same way. validate, analyze and revoke are dropped (live checks are out of scope by the threat model); confidence, skipReport, components and secretGroup/valueGroup are kept.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Unit tests first: each supported function and operator, both naming styles, and a rule whose filter uses anything unknown makes the sync fail and names the rule (no rule is vendored without its filter)
- [x] #2 Running it against v1.9.0 and v2.0.0-rc.2 converts every rule or fails loudly; the result for v1.9.0 is committed
- [x] #3 scripts/check_vendored_rules.py and tests/test_vendored_rules.py cover the new files the way they cover gitleaks
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
scripts/sync_betterleaks.py vX.Y.Z [--check] fetches config/betterleaks.toml and LICENSE at the tag, parses each filter/prefilter expression (both filter.X v1.9 names and v2 names; let, ternary, slices, lists, raw strings, word operators) into a JSON tree, drops validate/analyze/revoke, maps valueGroup to secretGroup, and fails naming the rule on an unknown function, token or rule field. v1.9.0 (463 rules) and v2.0.0-rc.2 (466 rules) both convert; v1.9.0 is vendored (regenerated from the script, byte-identical). check_vendored_rules.py and its tests cover the four new files (version pairing, no rules, rule without id). The detector does not read betterleaks.json yet (TASK-19.2).
<!-- SECTION:FINAL_SUMMARY:END -->
