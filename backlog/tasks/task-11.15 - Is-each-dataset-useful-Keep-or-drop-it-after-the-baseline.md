---
id: TASK-11.15
title: Is each dataset useful? Keep or drop it after the baseline
status: Done
assignee: []
created_date: '2026-10-11 11:16'
updated_date: '2026-10-11 14:36'
labels:
  - benchmark
  - dataset
dependencies:
  - TASK-11.9
  - TASK-16
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
- [x] #1 Per-dataset table: in-scope share and count, baseline P/R per type, rules firing, rules firing only there, probe sensitivity, overlap with other datasets
- [x] #2 Keep/drop recommendation per dataset in the inbox
- [x] #3 docs/BENCHMARK.md records the decision
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done 2026-10-11: maisecrets_bench/usefulness.py (rescore without rules from saved detections; table: scope, baseline per type, rules firing / only here, probe deltas; same_direction overlap), bench/usefulness.py CLI writes usefulness.md into the run. run.py saves detections.parquet (no values) and datasets.json. Scoring fix found by the probes: a dataset judges only the types it annotates (CredData: SECRET), spec updated. Result in the inbox (TASK-16); waiting for the keep/drop decision (AC2, AC3).

User decision 2026-10-11 (chat): 'TAB seems useless' -> dropped from the default setup and runs; adapter kept for --only tab. Recorded in docs/BENCHMARK.md. Code change after the running round-1 judge job finishes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
usefulness.py and bench/usefulness.py built; first full check: CredData and Gretel keep, TAB drop candidate. User decision 2026-10-11: TAB dropped (default setup and runs leave it out, adapter kept); recorded in docs/BENCHMARK.md.
<!-- SECTION:FINAL_SUMMARY:END -->
