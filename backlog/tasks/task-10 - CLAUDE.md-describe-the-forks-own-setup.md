---
id: TASK-10
title: 'CLAUDE.md: describe the fork''s own setup'
status: Done
assignee: []
created_date: '2026-10-11 07:56'
updated_date: '2026-10-11 09:33'
labels:
  - docs
dependencies: []
priority: low
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
origin is the personal GitHub fork; the GitLab pipeline, the release/mirror jobs and the marketplace notification never run for it. Rewrite the parts of CLAUDE.md that assume the upstream maintainer's setup (where the code lives, push rarely because of pipelines, release bumps, the GitLab CI notes) so an agent working here follows what actually applies. Do not delete .gitlab-ci.yml or the release scripts; only the guidance changes. Also note: run scripts/install-hooks.sh after a fresh clone (it was missing in this clone until 2026-10-11).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CLAUDE.md says which remote is origin and that the GitLab CI and release flow do not run for the fork
- [x] #2 The check list in CLAUDE.md names only checks that can run here
- [x] #3 CLAUDE.md tells to run scripts/install-hooks.sh after cloning
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
CLAUDE.md now describes the fork: origin is the user's public GitHub fork of Mcpgate-de/maisecrets (no handle in the file: the repo is public), upstream's GitLab pipeline, release and mirror never run here, keep .gitlab-ci.yml and the release scripts, upstream changes go as a GitHub PR after asking, run scripts/install-hooks.sh after a clone. Versions: the fork does not release. Push rule: only when the user says so; a push to main starts .github ci.yml (Windows + macOS; Actions enabled on the fork, no run yet). Check list: every check runs here (uvx ruff, claude plugin test added). Read-first now says C1 to C25. Checks: lint_plugin, derived_counts, scan_tree green; full suite runs in the pre-commit hook.
<!-- SECTION:FINAL_SUMMARY:END -->
