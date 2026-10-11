---
id: TASK-4
title: Plug terms into detect.rules() with stable entity placeholders
status: To Do
assignee: []
created_date: '2026-10-11 07:00'
labels:
  - terms
  - integration
dependencies:
  - TASK-3
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
New loader beside the existing ones in maisecrets/detect.py rules(); placeholder per entity label (e.g. PERSON_A) consistent across documents and sessions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A term in a prompt is blocked/rewritten, in a tool result redacted, in a tool call input rehydrated per existing policy
- [ ] #2 Same entity always maps to the same placeholder
- [ ] #3 No terms.txt -> behaviour identical to upstream (all existing tests green)
- [ ] #4 Integration test through the hook entry points with a temp home (tests/_isolate.py)
<!-- AC:END -->
