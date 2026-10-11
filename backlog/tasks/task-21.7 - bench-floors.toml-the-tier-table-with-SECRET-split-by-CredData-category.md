---
id: TASK-21.7
title: 'bench/floors.toml: the tier table, with SECRET split by CredData category'
status: Done
assignee: []
created_date: '2026-10-11 21:53'
updated_date: '2026-10-11 23:39'
labels:
  - benchmark
dependencies:
  - TASK-11.33
  - TASK-11.34
  - TASK-11.35
  - TASK-11.37
parent_task_id: TASK-21
priority: high
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A data file the scorer reads: tiers (critical 0.999, high 0.99, default no regression, none), the types each tier holds, the default for an unlisted type, and the dataset weights. SECRET is one type over 278 labels; a high floor cannot hold for generic keyword passwords. Split it for scoring by the CredData category column (token, password, key and others) and by rule kind (prefixed token vs keyword or generic), so prefixed tokens sit in critical and generic credentials in default. A test fails when a label table maps to a type that floors.toml neither lists nor covers by the default, and when a tier names an unknown type.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 floors.toml holds the tiers and weights the user decided; SECRET is split into at least prefixed and generic
- [x] #2 Tests: an unknown type in floors.toml fails; every type in the label tables resolves to a tier
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bench/floors.toml and maisecrets_bench/floors.py. Tiers as the user decided 2026-10-11: critical 0.999 (IBAN, CARD, US_SSN, US_BANK_NUMBER, SECRET_PREFIXED), high 0.99 (EMAIL, PHONE, IP, ABA, the German tax and ID types), default no_regression (SECRET_GENERIC and every unlisted type), none. CH_AHV and the Swiss IDs join when TASK-20 adds the types. SECRET splits for scoring: a CredData category is prefixed when a part names a vendor token with a fixed shape (36 parts listed), other datasets' SECRET labels are generic unless listed. Weights: gretel 2.0 and findocs 2.0, the proposal of TASK-21.1; the user's confirmation is TASK-21.1 AC 2 (inbox TASK-17). Tests: unknown type, SECRET in a tier, a type in two tiers, every label table type resolves, every prefixed part is a CredData part.
<!-- SECTION:FINAL_SUMMARY:END -->
