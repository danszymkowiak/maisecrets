---
id: TASK-34.5
title: 'redact: the vote and the human review gate (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - redact
  - tdd
dependencies:
  - TASK-34.3
  - TASK-34.4
parent_task_id: TASK-34
priority: high
ordinal: 91000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
How the results combine. Deterministic hits redact; model spans redact when every configured model agrees (overlap and type), and any disagreement goes to review. Review: an interactive prompt on a terminal (accept, reject, edit the span) and, without a terminal, a review file next to the output (<file>.review.json: position, type, which models agreed, the surrounding words with the value masked) that a second run applies. Nothing is released while a review is open unless --no-review is given (redacting every disputed span) or --accept-all.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first: unanimous -> redacted; split -> a review item; a review file applied by a second run gives the same output as the interactive answers
- [ ] #2 A run with open review items writes no redacted output and exits non-zero, unless --no-review or --accept-all
<!-- AC:END -->
