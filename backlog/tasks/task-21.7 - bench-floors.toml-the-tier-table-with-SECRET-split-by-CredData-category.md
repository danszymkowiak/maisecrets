---
id: TASK-21.7
title: 'bench/floors.toml: the tier table, with SECRET split by CredData category'
status: To Do
assignee: []
created_date: '2026-10-11 21:53'
labels:
  - benchmark
dependencies: []
parent_task_id: TASK-21
priority: high
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A data file the scorer reads: tiers (critical 0.999, high 0.99, default no regression, none), the types each tier holds, the default for an unlisted type, and the dataset weights. SECRET is one type over 278 labels; a high floor cannot hold for generic keyword passwords. Split it for scoring by the CredData category column (token, password, key and others) and by rule kind (prefixed token vs keyword or generic), so prefixed tokens sit in critical and generic credentials in default. A test fails when a label table maps to a type that floors.toml neither lists nor covers by the default, and when a tier names an unknown type.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 floors.toml holds the tiers and weights the user decided; SECRET is split into at least prefixed and generic
- [ ] #2 Tests: an unknown type in floors.toml fails; every type in the label tables resolves to a tier
<!-- AC:END -->
