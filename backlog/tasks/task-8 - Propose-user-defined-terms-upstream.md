---
id: TASK-8
title: Propose user-defined terms upstream
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-11 09:33'
labels:
  - upstream
dependencies:
  - TASK-7
priority: low
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
File a feature request on Mcpgate-de/maisecrets (via /maisecrets:report) so the fork can be dropped if merged. Outward-facing: confirm with the user first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 User approved the issue text before it is filed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11 (run): the fork raised the Python floor to 3.12 (TASK-9, 2a77302) and dropped the unit_python39 job from .gitlab-ci.yml. Upstream supports 3.9 (stock macOS). A change offered upstream must leave that out: build the terms commits on upstream's main without TASK-9, and run the suite under 3.9 (uv has cpython-3.9 here; the terms code passed 1110 tests on 3.9 before TASK-9).
<!-- SECTION:NOTES:END -->
