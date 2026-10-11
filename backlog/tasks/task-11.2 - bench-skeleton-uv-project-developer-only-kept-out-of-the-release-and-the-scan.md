---
id: TASK-11.2
title: >-
  bench/ skeleton: uv project, developer-only, kept out of the release and the
  scan
status: Done
assignee: []
created_date: '2026-10-11 10:20'
updated_date: '2026-10-11 11:16'
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
- [x] #1 uv run --project bench python -c 'import pyarrow' works
- [x] #2 release tree test counts bench/ as developer-only
- [x] #3 ruff and scan_tree pass with bench/
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/: uv project (pyarrow, datasets; requires-python >=3.12) with uv.lock, maisecrets_bench.paths (data dir from MAISECRETS_BENCH_DATA, default ~/.cache/maisecrets-bench, refused inside the repo), bench/tests (4 tests), README stub. bench/ developer-only in tests/test_release_tree.py (builder allowlist already excludes it); bench/.venv ignored; scan_tree skips .venv (it had read 4,555 files of installed packages); ruff lists in CLAUDE.md, pre-push, .gitlab-ci.yml include bench; CLAUDE.md check list runs the bench tests. Checks: bench tests OK, release-tree test OK at HEAD, scan_tree 0, lint, counts, ruff green; full suite ran in the pre-commit hook.
<!-- SECTION:FINAL_SUMMARY:END -->
