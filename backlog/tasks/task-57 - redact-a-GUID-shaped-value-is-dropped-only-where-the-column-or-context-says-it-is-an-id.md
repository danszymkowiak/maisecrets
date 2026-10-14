---
id: TASK-57
title: >-
  redact: a GUID-shaped value is dropped only where the column or context says
  it is an id
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
labels:
  - redact
dependencies: []
ordinal: 118000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14: plausible() drops every model span on a GUID shape anywhere, so a UUID-shaped API key or customer id in free text that a model calls SECRET or ACCOUNT is written in the clear. Keep the drop for columns named like ids (guid, uuid, id, *_id) and for a model label of NATIONAL_ID/ACCOUNT on a bare GUID in a table; send a GUID in free text with a SECRET label to review instead.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A GUID under guid/uuid/id headers is never redacted by a model span
- [ ] #2 A GUID-shaped value a model labels SECRET in free text goes to review, with a test
- [ ] #3 The synthetic Firefox export of TASK-50 still keeps every GUID
<!-- AC:END -->
