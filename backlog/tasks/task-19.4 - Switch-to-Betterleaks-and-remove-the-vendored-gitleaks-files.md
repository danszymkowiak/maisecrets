---
id: TASK-19.4
title: Switch to Betterleaks and remove the vendored gitleaks files
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 10:43'
labels:
  - detection
  - plugin
dependencies:
  - TASK-19.3
  - TASK-19.8
parent_task_id: TASK-19
priority: high
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Once TASK-19.3 accepts the change: make Betterleaks the only secret rule source from upstream, remove gitleaks.toml, gitleaks.json, LICENSE-gitleaks, GITLEAKS_VERSION and scripts/sync_gitleaks.py. Update everything that names gitleaks: tests (test_core, test_detect_rules, test_vendored_rules, test_skill: the skill bundle expects rules/gitleaks.toml, test_static_python), NOTICE, README (vendored sources, refresh command), the CLI version line (maisecrets/cli.py:368), docs/REPO-STANDARDS.md, the bench (detector.py, curves.py, the entropy-curve section of docs/BENCHMARK.md), labels/en.txt and prefixes.txt comments. renovate.json and .gitlab-ci.yml stay unchanged (fork only).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No gitleaks rule file is vendored; NOTICE and README name Betterleaks, its licence and version
- [ ] #2 The full check list in CLAUDE.md passes, including derived_counts.py and the harness
- [ ] #3 The commit subject is written for the changelog (for example deps(rules): ...)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Gate from TASK-19.2: switch only when the unit suite passes with Betterleaks (run it in-process with tests/_isolate imported first; see TASK-19.3's notes for the 3 known differences).

From TASK-19.3: switch only on an accepted verdict of TASK-19.8. When gitleaks goes: datadog-access-token is let go (Betterleaks' datadog-application-key takes the shape); etsy-access-token, jfrog-api-key and jfrog-identity-token are carried as our own rules (Betterleaks misses them with only a provider label).
<!-- SECTION:NOTES:END -->
