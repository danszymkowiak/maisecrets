---
id: TASK-34.5
title: 'redact: the vote and the human review gate (test first)'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:47'
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
- [x] #1 Tests first: unanimous -> redacted; split -> a review item; a review file applied by a second run gives the same output as the interactive answers
- [x] #2 A run with open review items writes no redacted output and exits non-zero, unless --no-review or --accept-all
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
review.decide() (pure): rule hits redact; model spans inside a rule hit are covered; overlapping model spans form a group that is redacted (as their union) when every configured model holds a span of one common type in it, else a review item. review.items() builds the open items with position, type, models agreed and missing, and a context where every other decided value shows as [TYPE] and the item as [TYPE?]; the review file (<output>.review.json) holds them with decision null and a hash of the document; read_file refuses a changed document (StaleReview). app.run_file(): extract, rules, models, vote; open items are redacted with --no-review/--accept-all, asked at a terminal, or written to the review file (no output, exit 3) until every item says redact or keep. cli.py builds the model detectors when the extra is installed (--models, --accept-model-terms, --rules-only); its prompt never prints a value. Tests with fake models: unanimous vs split, rules covering model spans, no output while open, the review file and terminal answers give the same output, keep, --no-review, stale refusal. docs/REDACT.md: Review.
<!-- SECTION:FINAL_SUMMARY:END -->
