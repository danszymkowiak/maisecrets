---
id: TASK-17
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 17:43'
updated_date: '2026-10-11 17:44'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 17:44
---
TASK-11.28..11.31: four plugin changes passed the bench (round 2, TASK-11.17): us-bank bank word just before the number (+1.10 dev / +1.15 check, within tolerance), se-personnummer and it-fiscal-code checksums (small, within tolerance), keyword rules skipping UPPER-UPPER-..._ identifiers and digits:word values (strict on dev, but zero effect on check: the shapes sit in a few dev files), drop uk-postcode (strict everywhere). Options: (a) approve all four; (b) approve some (name them); (c) none yet. I recommend (a): each gets a can-fail belief and a bench rerun; the identifier filter's dev-only evidence is the weakest, so (b) without TASK-11.30 is the cautious choice.
---

created: 2026-10-11 17:44
---
Tolerance (TASK-11.16): 'score not lower on every dataset' rejects changes over ai4privacy score drops of 0.01 points (one or two finds of ~250,000): skip UPPER_lower identifiers (+0.82 dev, CredData +2.45), us-passport and us-license context words. Options: (a) keep it as is; (b) allow a dataset's score to fall by at most 0.05 points when the mean rises; (c) allow it on guard datasets only. I recommend (b): 0.05 points is below one find per 2,000 on every scored dataset and the mean must still rise; the reports keep showing the loss.
---

created: 2026-10-11 17:44
---
TASK-11.17 family C: about 1,300 of ai4privacy's dev false alarms (email 1,005, ip 318, phone 20) are values at offset 0 of a continuation record (ids ...B, ...C) that ai4privacy's own chunking left unlabelled; another ~2,300 are values its generator wrote outside the injected slots. Options: (a) the scorer leaves a detection at offset 0 of a continuation record uncounted (neutral) and reports state that ai4privacy precision is a lower bound; (b) only the lower-bound note; (c) nothing. I recommend (a): the first group is a provable gap of the dataset; the second cannot be split from real false alarms without reading text.
---
<!-- COMMENTS:END -->
