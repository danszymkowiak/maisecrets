---
id: TASK-11.15
title: Is each dataset useful? Keep or drop it after the baseline
status: To Do
assignee: []
created_date: '2026-10-11 11:16'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.9
parent_task_id: TASK-11
priority: medium
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User request 2026-10-11: a dataset may be useless here, being saturated or out of scope, and should then be excluded. After the first baseline run (TASK-11.9), report per dataset: (1) scope, meaning the share of gold positives that map to a maisecrets type, and the count of in-scope positives; (2) saturation, meaning baseline precision and recall per type (both near 1.0 means little room to show a change); (3) discrimination, meaning how many rules fire on it and how many rules fire only there, and whether a set of probe mutations (disable each of the top-firing rules; loosen/tighten a threshold) moves its score at all; (4) overlap, meaning whether its score moves the same way as another dataset's on the probes (redundant if always identical). Recommend keep/drop per dataset with the numbers; the decision goes to the user via the inbox. A dropped dataset leaves the equal-weight mean.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Per-dataset table: in-scope share and count, baseline P/R per type, rules firing, rules firing only there, probe sensitivity, overlap with other datasets
- [ ] #2 Keep/drop recommendation per dataset in the inbox
- [ ] #3 docs/BENCHMARK.md records the decision
<!-- AC:END -->
