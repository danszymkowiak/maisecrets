---
id: TASK-36
title: 'Bench: findocs labels its generated names, birth dates and street lines'
status: Done
assignee: []
created_date: '2026-10-12 15:06'
updated_date: '2026-10-12 17:53'
labels:
  - bench
dependencies: []
priority: medium
ordinal: 97000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by TASK-34.8 (2026-10-12): findocs writes a generated name into almost every document (Arbeitnehmer, Kontoinhaber, Bill to, MT940 ?32) and labels none, so redact's models were charged a false positive for each name they found; birth dates (Geburtsdatum, Date de naissance) were labelled neg DATE; employer street lines were unlabelled. Label them pos, out of scope for the plugin (no change to its recall; a plugin hit there becomes neutral instead of a false positive): NAME, COMPANY, DOB, ADDRESS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every generated name, company, birth date and street line of findocs is a pos span (OUT_OF_SCOPE), tested
- [x] #2 The dataset is rebuilt; the plugin baseline and redact's measurement are re-run on it
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
findocs labels its generated names, companies, birth dates and street lines as positives out of the plugin's scope (a90cfbd; texts unchanged). Rebuilt; redact re-scored (false redactions about halved, docs/REDACT.md) and the plugin baseline re-run: 20261012-194832, mean 84.4 %.
<!-- SECTION:FINAL_SUMMARY:END -->
