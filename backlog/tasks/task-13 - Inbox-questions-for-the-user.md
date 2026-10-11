---
id: TASK-13
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 08:27'
updated_date: '2026-10-11 08:27'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 08:27
---
TASK-11: which labelled sets should the precision/recall scorecard use, and how should their labels map onto our policy? Options: (a) synthetic only: ai4privacy PII + Presidio-generated data, plus a hand-made secret set; (b) add Samsung CredData (real leaked credentials, kept outside the repo, script prints counts only); (c) also SecretBench/i2b2 (access by request or a data-use agreement). I recommend (a) then (b) because (a) has no licence or leak risk and gives recall numbers at once, and CredData adds real secret shapes; its fixture labels (e.g. hunter2) need mapping to NO_HIT. Also: should terms.txt get its own labelled set (Polish names with inflection)?
---
<!-- COMMENTS:END -->
