---
id: TASK-11.26
title: >-
  Experiment: decode base64 and hex blobs and rescan them, with depth, size and
  time caps
status: To Do
assignee: []
created_date: '2026-10-11 17:07'
labels:
  - benchmark
dependencies:
  - TASK-11.19
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: medium
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 7. The store matches encoded forms of values it knows, but nothing decodes an unknown blob. Candidates: base64 runs of 24+ characters or hex of 32+, valid length and padding, at least 90% printable after decoding, depth at most 2, a cap on candidates and decoded bytes, a hard time slice. Targets: Authorization: Basic (the auth-scheme rule needs 16+ characters, so a short encoded pair is missed), kubectl Secret data:, docker config.json auth, .npmrc _auth, JWT payloads (claims may hold an e-mail), gzip+base64 at depth 2. A hit inside decoded text redacts the whole encoded run.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Recall on the synthetic dataset's encoded pos spans and on the base64/hex perturbations, before and after
- [ ] #2 No precision loss on CredData and Gretel beyond tolerance; decoded bytes and time per scan reported at p50 and worst case
- [ ] #3 A test that a 1 MB base64 blob stays within the time slice
<!-- AC:END -->
