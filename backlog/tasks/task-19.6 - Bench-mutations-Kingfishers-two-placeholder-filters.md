---
id: TASK-19.6
title: 'Bench mutations: Kingfisher''s two placeholder filters'
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
labels:
  - benchmark
  - false-positive
dependencies:
  - TASK-19.4
parent_task_id: TASK-19
priority: medium
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two false-positive filters Kingfisher adds to Betterleaks rules (data/imported-rules-capabilities.md, Placeholder exclusions): (1) private-key: drop a PEM-shaped hit with fewer than 64 characters between BEGIN and END; (2) mongodb-connection-string: drop a hit whose password is only a variable reference ($(NAME), ${NAME}, $NAME, {{ NAME }}). Check first whether the detector already drops either (looks_like_placeholder, the global template filter); write mutations only for what it does not.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each filter is either shown to exist already, or judged as a mutation on dev and check
- [ ] #2 Accepted filters become plugin changes, each with a test
<!-- AC:END -->
