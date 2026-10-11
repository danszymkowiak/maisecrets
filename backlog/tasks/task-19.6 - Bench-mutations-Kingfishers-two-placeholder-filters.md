---
id: TASK-19.6
title: 'Bench mutations: Kingfisher''s two placeholder filters'
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-11 22:45'
labels:
  - benchmark
  - false-positive
dependencies:
  - TASK-19.4
  - TASK-19.7
parent_task_id: TASK-19
priority: medium
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two false-positive filters Kingfisher adds to Betterleaks rules (data/imported-rules-capabilities.md, Placeholder exclusions): (1) private-key: drop a PEM-shaped hit with fewer than 64 characters between BEGIN and END; (2) mongodb-connection-string: drop a hit whose password is only a variable reference ($(NAME), ${NAME}, $NAME, {{ NAME }}). Check first whether the detector already drops either (looks_like_placeholder, the global template filter); write mutations only for what it does not.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each filter is either shown to exist already, or judged as a mutation by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens)
- [ ] #2 Accepted filters become plugin changes, each with a test
<!-- AC:END -->
