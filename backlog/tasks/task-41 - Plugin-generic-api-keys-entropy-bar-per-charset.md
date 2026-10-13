---
id: TASK-41
title: 'Plugin: generic-api-key''s entropy bar per charset'
status: Done
assignee: []
created_date: '2026-10-12 20:59'
updated_date: '2026-10-13 21:08'
labels:
  - plugin
dependencies: []
priority: medium
ordinal: 102000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-11.21: raw Shannon entropy compared with one threshold per detected charset (hex 3.449, base32 3.584, base62 3.322, base64 3.252, base64url 3.426, printable 3.594; chosen on dev) in place of one 3.5. Judged on baseline 20261012-194832 (bench/mutations/round5/entropy-charset.toml): accepted, SECRET_GENERIC +112 finds, 11 fewer false positives. An alternative to TASK-40's flat 3.3 for generic-api-key (+259 finds for +101 false positives); the two should not both be applied without judging them together. Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 generic-api-key compares entropy per charset; tests per charset at the threshold and below
- [x] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Applied in 795b411 together (user: judge together before applying): credit-card stands alone after Luhn, generic-api-key uses the per-charset entropy floors (TASK-41) in place of a flat 3.3. Guards: a + before the number, published test cards without a card word. Judge round7 against 20261013-222047 accepted (after the bench fix aae95d0); bench run 20261013-225445: CARD +310, SECRET_GENERIC +112, US_BANK_NUMBER +12, FP +44. Unit tests, replay_can_fail, ruff green.
<!-- SECTION:FINAL_SUMMARY:END -->
