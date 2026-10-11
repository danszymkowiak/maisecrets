---
id: TASK-5
title: 'Leak tests: term text never appears in logs, audit, errors or reports'
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
labels:
  - terms
  - security
  - tdd
dependencies:
  - TASK-4
priority: high
ordinal: 5000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Audit log, events, incident records, /maisecrets:report text and every error path contain the placeholder or line number, never a term
- [ ] #2 /maisecrets:list and status show counts/labels only
- [ ] #3 scripts/scan_tree.py still clean
<!-- AC:END -->
