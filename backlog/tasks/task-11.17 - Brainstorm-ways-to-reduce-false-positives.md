---
id: TASK-11.17
title: Brainstorm ways to reduce false positives
status: To Do
assignee: []
created_date: '2026-10-11 15:46'
labels:
  - benchmark
  - design
dependencies: []
parent_task_id: TASK-11
priority: medium
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-11. Most of the lost score is false alarms: Gretel precision 75.1% (us-bank alone ~4,000 FPs), CredData 78.6%. Brainstorm approaches beyond dropping single rules, with the bench to measure each: tighter context windows and context words per rule, paired changes (drop a rule and tighten its neighbour so the finds come back), checksums or validators (routing ABA, IBAN, Luhn) where a rule lacks one, entropy thresholds (bench/curves.py), shape filters for prose and code words, and which false alarms are acceptable for a redaction tool. Use bench/round.py brief and bench/errors.py (masked) as input; the outcome is a ranked list of candidate changes as backlog tasks or mutation files.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A written list of approaches, each with the false alarms it targets (rule, count on dev) and its risk to recall
- [ ] #2 The most promising become backlog tasks or bench/mutations files, judged with bench/round.py judge
<!-- AC:END -->
