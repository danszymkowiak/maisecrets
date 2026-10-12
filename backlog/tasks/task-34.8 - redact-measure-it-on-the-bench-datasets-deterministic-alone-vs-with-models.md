---
id: TASK-34.8
title: 'redact: measure it on the bench datasets (deterministic alone vs with models)'
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - redact
  - bench
dependencies:
  - TASK-34.5
parent_task_id: TASK-34
priority: medium
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The bench (bench/, TASK-30 clean gold) already labels names and addresses, which the plugin does not detect. Run the tool's detection over findocs, Gretel, Nemotron and Mendeley: recall and false positives per type for the deterministic pass alone, each model alone, and the vote; time per document on CPU. The spec notes that published model scores do not transfer to German financial and legal prose: this answers it on our own data. Licence rules of the bench apply (ai4privacy stays local).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A report per configuration (deterministic, each model, vote) with recall and false positives per type and time per document
- [ ] #2 docs/REDACT.md records the default model set chosen from it
<!-- AC:END -->
