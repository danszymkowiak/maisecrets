---
id: TASK-19.8
title: >-
  Bench: Betterleaks with gitleaks' generic-api-key carried over, and its
  npm-access-token checked
status: To Do
assignee: []
created_date: '2026-10-12 10:43'
labels:
  - bench
  - detection
dependencies:
  - TASK-19.3
parent_task_id: TASK-19
priority: high
ordinal: 96000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-19.3 (docs/BENCHMARK.md, Betterleaks against gitleaks): the switch is rejected by two rules only. Betterleaks' generic-api-key adds about 420 false hits on CredData and has no password keyword (the synthetic guard loses about 24 finds); its npm-access-token misses the 4 synthetic npm tokens that gitleaks' rule finds. Everything else gains (+22 SECRET_PREFIXED, 1 new false hit, and gcp-service-account is off). Bench: Betterleaks with its generic-api-key off and gitleaks' generic-api-key carried (its regex, keywords, entropy 3.5 and allowlists, through the bench's add op or a carried-rules file), and npm-access-token compared on the 4 misses (shape, keyword, filter). Then the verdict decides TASK-19.4.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The cause of the 4 npm misses is named, with a fix or a carried rule
- [ ] #2 A mutation with the carried generic-api-key and the npm fix is judged: accepted, or the remaining loss is named
<!-- AC:END -->
