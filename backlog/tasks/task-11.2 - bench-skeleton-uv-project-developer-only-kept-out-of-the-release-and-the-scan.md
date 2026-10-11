---
id: TASK-11.2
title: >-
  bench/ skeleton: uv project, developer-only, kept out of the release and the
  scan
status: To Do
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:06'
labels:
  - benchmark
dependencies: []
parent_task_id: TASK-11
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bench/pyproject.toml (uv; pyarrow, datasets, pandas or polars) separate from the plugin, which stays dependency-free. bench/ is developer-only in tests/test_release_tree.py and scripts/build_release_tree.py; data dir is never under the repo. ruff covers bench/.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv run --project bench python -c 'import pyarrow' works
- [ ] #2 release tree test counts bench/ as developer-only
- [ ] #3 ruff and scan_tree pass with bench/
<!-- AC:END -->
