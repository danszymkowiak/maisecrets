---
id: TASK-41
title: 'Plugin: generic-api-key''s entropy bar per charset'
status: To Do
assignee: []
created_date: '2026-10-12 20:59'
labels:
  - plugin
dependencies:
  - TASK-17
priority: medium
ordinal: 102000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-11.21: raw Shannon entropy compared with one threshold per detected charset (hex 3.449, base32 3.584, base62 3.322, base64 3.252, base64url 3.426, printable 3.594; chosen on dev) in place of one 3.5. Judged on baseline 20261012-194832 (bench/mutations/round5/entropy-charset.toml): accepted, SECRET_GENERIC +112 finds, 11 fewer false positives. An alternative to TASK-40's flat 3.3 for generic-api-key (+259 finds for +101 false positives); the two should not both be applied without judging them together. Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 generic-api-key compares entropy per charset; tests per charset at the threshold and below
- [ ] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->
