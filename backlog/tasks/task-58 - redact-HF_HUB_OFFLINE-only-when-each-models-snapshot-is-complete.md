---
id: TASK-58
title: 'redact: HF_HUB_OFFLINE only when each model''s snapshot is complete'
status: To Do
assignee: []
created_date: '2026-10-14 07:16'
labels:
  - redact
dependencies: []
ordinal: 119000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review 2026-10-14: library_env sets HF_HUB_OFFLINE when snapshots/ holds any entry. An interrupted first download, or a model fetched without its base encoder (GLiNER's config.model_name), then fails on every later run with a 'not in local cache' error that does not say the tool turned offline mode on.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Offline only when each model's snapshot has its config and weight files (and a GLiNER model's base encoder is cached)
- [ ] #2 A load that fails while the tool set offline mode says so and how to finish the download
<!-- AC:END -->
