---
id: TASK-11.20
title: >-
  Experiment: suppress digest, integrity and object-id shapes unless a secret
  label is near
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.18
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 1 (cheapest, lowest risk). Pure hex of 32/40/56/64/96/128 characters is almost always an MD5/SHA digest or git object id; sha256:, sha512-<base64>==, h1: and integrity= strings fill lockfiles and docker digests; 24-hex is a MongoDB ObjectId. A bench filter drops such a value on entropy-only and generic rules unless a strong secret label sits before it (legacy bare-hex keys must stay hits); prefix-shaped vendor tokens are never filtered. CredData keeps the shape of its values, so digest negatives may be rare there: judge on CredData and on the synthetic dataset's neg spans.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One mutation per shape family (hex lengths, prefixed digests, ObjectId) and one combined, judged with bench/round.py judge on dev and check
- [ ] #2 Counts of false alarms removed and finds lost per rule, from bench/errors.py (masked)
- [ ] #3 Re-judged on the synthetic tool-output dataset once TASK-11.19 lands; a passing change becomes a plugin task with a can-fail belief
<!-- AC:END -->
