---
id: TASK-11.20
title: >-
  Experiment: suppress digest, integrity and object-id shapes unless a secret
  label is near
status: In Progress
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-11 17:49'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11 probe (run 20261011-173619, counts only): on generic-api-key and ds-* rules, CredData hex-digest-shaped values (32/40/56/64/96/128 hex, 24-hex ObjectId) are real secrets: 2,591 TP vs 87 FP. By the label before the value: strong secret label 451 TP / 32 FP; other labels (key, ...) 2,137 TP / 54 FP; a digest label (hash, sha, checksum, integrity, etag, commit, ...) 3 TP / 1 FP. So 'drop unless a strong label' would cost ~2,100 finds; only 'drop when the label names a digest' is safe, and it is tiny on CredData. Prefixed digests (sha256:, sha512-, h1:) never matched these rules on the corpora. Next: the synthetic dataset's run decides whether digests are false alarms in tool output at all.
<!-- SECTION:NOTES:END -->
