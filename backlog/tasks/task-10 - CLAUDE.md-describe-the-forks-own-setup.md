---
id: TASK-10
title: 'CLAUDE.md: describe the fork''s own setup'
status: To Do
assignee: []
created_date: '2026-10-11 07:56'
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
- [ ] #1 CLAUDE.md says which remote is origin and that the GitLab CI and release flow do not run for the fork
- [ ] #2 The check list in CLAUDE.md names only checks that can run here
- [ ] #3 CLAUDE.md tells to run scripts/install-hooks.sh after cloning
<!-- AC:END -->
