---
id: TASK-58
title: 'redact: HF_HUB_OFFLINE only when each model''s snapshot is complete'
status: Done
assignee: []
created_date: '2026-10-14 07:16'
updated_date: '2026-10-14 08:13'
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
- [x] #1 Offline only when each model's snapshot has its config and weight files (and a GLiNER model's base encoder is cached)
- [x] #2 A load that fails while the tool set offline mode says so and how to finish the download
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
models.cached(): the snapshot refs/main names holds a config and weights; a GLiNER model without its own tokenizer also needs its base encoder's config, a bi-encoder its labels encoder. library_env sets HF_HUB_OFFLINE only then. load() turns a failure under the offline mode it set into a RuntimeError that says so and asks for one run with HF_HUB_OFFLINE=0. The four defaults in this machine's cache still count as complete. Tests: CompleteSnapshotTests.
<!-- SECTION:FINAL_SUMMARY:END -->
