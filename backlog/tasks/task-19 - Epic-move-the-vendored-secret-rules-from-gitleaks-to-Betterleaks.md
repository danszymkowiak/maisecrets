---
id: TASK-19
title: 'Epic: move the vendored secret rules from gitleaks to Betterleaks'
status: To Do
assignee: []
created_date: '2026-10-11 21:30'
labels:
  - epic
  - detection
  - false-positive
dependencies: []
references:
  - 'https://github.com/betterleaks/betterleaks'
  - 'https://github.com/mongodb/kingfisher'
  - >-
    research_notes/Deterministic redaction detection
    ideas/token_structure_and_engines.md
priority: high
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided with the user 2026-10-11. gitleaks has not released since v8.30.1 (2026-03-21); its author now maintains Betterleaks (MIT, github.com/betterleaks/betterleaks). Betterleaks v1.9.0 (2026-09-29) has 463 rules against the 222 vendored from gitleaks: 245 new, and only 4 gitleaks rules missing (datadog-access-token, etsy-access-token, jfrog-api-key, jfrog-identity-token). v2.0.0-rc.2 (2026-10-07) keeps the same TOML and renames the filter functions (filter.entropy -> entropy); its notes warn the config may still change.

The main goal is fewer false positives, not more rules. The user's highest-risk content is tax documents, financial data and other personal documents, so a new rule is kept only when the bench shows no precision loss, with Gretel (finance), TAB and the synthetic tool output as guards.

Scope: fork only. renovate.json and .gitlab-ci.yml stay as upstream has them (they do not run here); offering this upstream would need them updated and is not part of this epic. Ordering: this runs before the leave-one-out review (TASK-18) continues, so that review runs once, on the new rule set.

From Kingfisher (mongodb/kingfisher, Apache-2.0): its 2.x catalogue is generated from pinned Betterleaks plus 26 selected Google Veles detectors, with an overlay of per-rule overrides. We take the Veles rules, its two placeholder filters and the overlay pattern; not its engine (Rust, Vectorscan) and not its live validation or revocation. Its bare (context-free) token variants are left out: they add matches and so add false-positive risk.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 gitleaks is no longer vendored; Betterleaks (pinned) is, plus the Veles rules that pass the bench
- [ ] #2 The bench report shows precision on every dataset equal or better than the gitleaks baseline, recall stated alongside
- [ ] #3 The leave-one-out review (TASK-18) resumes on the new rule set
<!-- AC:END -->
