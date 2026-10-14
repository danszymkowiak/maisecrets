---
id: TASK-55
title: 'redact: password-shaped tokens in free-text columns go to review'
status: To Do
assignee: []
created_date: '2026-10-14 07:04'
labels:
  - redact
dependencies:
  - TASK-51
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follows TASK-50/51 (user, 2026-10-14). A password with no context (a password manager's notes/extra column, a comment cell) matches no rule, header or model. Entropy alone does not find it: human passwords score low, while GUIDs, hashes and timestamps score high (see TASK-50). Instead, a password-shape check: one token of 8 to 64 characters, at least three character classes, not a dictionary word plus digits, not an ID shape (GUID, hash, date, timestamp, URL). Scoped to free-text columns (notes, comment, description, extra) and plain text; a hit adds a review item, never a redaction of its own. Measure on the bench before trusting it; synthetic values only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A pure function says whether a token has the password shape; tests cover hits, ID shapes, dictionary words with digits, and URLs
- [ ] #2 In a notes-like column or plain text a password-shaped token becomes a review item, never a redaction alone
- [ ] #3 The bench (or a synthetic fixture with prose, IDs and passwords) gives its finds and false hits per 1,000 words; it is kept only if the finds outweigh the false hits
- [ ] #4 docs/REDACT.md describes the check and its numbers
<!-- AC:END -->
