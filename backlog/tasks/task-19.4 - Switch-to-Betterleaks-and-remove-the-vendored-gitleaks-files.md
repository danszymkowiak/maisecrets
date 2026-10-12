---
id: TASK-19.4
title: Switch to Betterleaks and remove the vendored gitleaks files
status: Done
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 11:16'
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
- [x] #1 No gitleaks rule file is vendored; NOTICE and README name Betterleaks, its licence and version
- [x] #2 The full check list in CLAUDE.md passes, including derived_counts.py and the harness
- [x] #3 The commit subject is written for the changelog (for example deps(rules): ...)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Gate from TASK-19.2: switch only when the unit suite passes with Betterleaks (run it in-process with tests/_isolate imported first; see TASK-19.3's notes for the 3 known differences).

From TASK-19.3: switch only on an accepted verdict of TASK-19.8. When gitleaks goes: datadog-access-token is let go (Betterleaks' datadog-application-key takes the shape); etsy-access-token, jfrog-api-key and jfrog-identity-token are carried as our own rules (Betterleaks misses them with only a provider label).

From TASK-19.8: the accepted configuration is Betterleaks + gitleaks' generic-api-key carried (with its allowlists and fixes), plus etsy-access-token, jfrog-api-key and jfrog-identity-token carried (TASK-19.3), with generic-password, generic-credential-uri and gcp-service-account off (rules/overrides.txt). The carried rules need a home when gitleaks.json goes: a carried-rules file in rules/ (from gitleaks v8.30.1, MIT) loaded with the Betterleaks set.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Betterleaks v1.9.0 is the only vendored secret set (Settings.secret_rules and SECRET_RULES default 'betterleaks'). gitleaks.toml, gitleaks.json, GITLEAKS_VERSION and scripts/sync_gitleaks.py removed. Four gitleaks v8.30.1 rules are carried in maisecrets/rules/carried.json (generic-api-key in place of Betterleaks' own, per TASK-19.8; etsy-access-token, jfrog-api-key, jfrog-identity-token, per TASK-19.3), with LICENSE-gitleaks kept and NOTICE naming both; the loader puts a carried rule in place of Betterleaks' rule of that id. Off in overrides.txt: generic-password, generic-credential-uri, gcp-service-account. Updated: NOTICE, README, docs/REPO-STANDARDS.md, docs/BENCHMARK.md, cli status line, replay_sessions, check_vendored_rules (carried.json must name its gitleaks source), tests (detect_rules, vendored_rules, skill, static_python, betterleaks_rules, ruleset), bench (detector rule index, carry from 'carried', curves wording). renovate.json and .gitlab-ci.yml unchanged (fork only). Checks: 1197 unit tests OK, 108/108 beliefs, harness 0 failures, mod tests 16/16, bench tests, ruff, lint, scan, counts. Bench baseline 20261012-131230 against gitleaks 20261012-113809: accepted, CredData +8 true hits, nothing else moves.
<!-- SECTION:FINAL_SUMMARY:END -->
