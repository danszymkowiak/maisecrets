---
id: TASK-19.5
title: Vendor the Veles rules from Kingfisher for providers Betterleaks lacks
status: Done
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 12:20'
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
- [x] #1 A sync script pinned to a Kingfisher tag; NOTICE names Veles (Apache-2.0) and Kingfisher
- [x] #2 Rules that overlap a Betterleaks rule are skipped; each remaining rule is judged on the bench and kept or dropped with a reason
<!-- AC:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 21:58
---
Licence (user, 2026-10-11: the fork is public, so licences must hold for any user): Veles is Apache-2.0 and Kingfisher's catalogue is a modified derivative. Carry over the Veles attribution from Kingfisher's generated/NOTICES.txt and the upstream licence text, mark the rules as modified (Apache-2.0 4b), and record the pinned Veles revision from generated/provenance.json.
---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
scripts/sync_veles.py vX.Y.Z (run with uv run --with pyyaml) reads Kingfisher's generated veles.yml and provenance at the tag as data, keeps pattern, secret group, path and source, drops validation/revocation, refuses unknown fields, missing or non-compiling patterns naming the rule, and writes rules/veles.json (with the Kingfisher tag and the OSV-SCALIBR revision), LICENSE-kingfisher and VELES_VERSION; pinned to v2.11.1. detect._load_veles() appends them to the Betterleaks set. Overlap measured by scanning a generated sample of each rule: 8 covered by Betterleaks rules, 3 git URLs covered by ds-basic-auth, 3 no secrets (repository URLs, a client id): 14 off in overrides.txt with reasons. The remaining 12 fire on no bench sample (run 20261012-141549, neutral): kept. NOTICE names Veles (Google, Apache-2.0) and Kingfisher (MongoDB, Apache-2.0); README lists the source; check_vendored_rules covers the three files. Tests: tests/test_sync_veles.py.
<!-- SECTION:FINAL_SUMMARY:END -->
