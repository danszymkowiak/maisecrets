---
id: TASK-19.5
title: Vendor the Veles rules from Kingfisher for providers Betterleaks lacks
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
labels:
  - detection
  - benchmark
dependencies:
  - TASK-19.4
references:
  - >-
    https://github.com/mongodb/kingfisher/blob/v2.11.1/crates/kingfisher-rules/generated/rules/veles.yml
parent_task_id: TASK-19
priority: medium
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Kingfisher's generated/rules/veles.yml (at a pinned tag, v2.11.1 when this was written) holds 26 Google Veles (OSV-SCALIBR, Apache-2.0) detectors already converted from Go into plain regexes, chosen by Kingfisher where Betterleaks has no rule: Bitwarden, CodeCatalyst, CodeCommit and Bitbucket Git credentials, Deno, HCP, Packagist, OpenRouter and others. A sync script reads it as data, keeps pattern and named groups, drops validation and revocation, and writes a rule file with licence and provenance (the Veles revision is in Kingfisher's generated/provenance.json). Each rule enters only if the bench shows no precision loss.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A sync script pinned to a Kingfisher tag; NOTICE names Veles (Apache-2.0) and Kingfisher
- [ ] #2 Rules that overlap a Betterleaks rule are skipped; each remaining rule is judged on the bench and kept or dropped with a reason
<!-- AC:END -->
