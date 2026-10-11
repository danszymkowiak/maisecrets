---
id: TASK-19.3
title: 'Bench: Betterleaks against gitleaks, and what to do about tokenRatio'
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
labels:
  - benchmark
  - false-positive
dependencies:
  - TASK-19.2
references:
  - docs/BENCHMARK.md
parent_task_id: TASK-19
priority: high
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Run the switch from TASK-19.2 as a mutation and judge it with the bench's verdicts on dev and check. Precision comes first (the user's highest-risk content is tax, financial and personal documents): Gretel (finance), TAB and the synthetic tool output are guards. List every new rule that fires, with its true and false hits per dataset; a new rule with false hits and no true hits goes into the override file as disabled, with the reason.

Decide tokenRatio for its 124 rules, by bench numbers: (a) fall back to entropy, (b) the word-likeness stand-in from TASK-11.22, (c) drop those rules. The 4 rules only gitleaks has (datadog-access-token, etsy-access-token, jfrog-api-key, jfrog-identity-token) get a note: keep through prefixes.txt or the override file, or let them go.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A report with per-dataset precision and recall for both rule sets, and the new rules that fired, with their hits
- [ ] #2 The tokenRatio choice is made from measured numbers and recorded in the report
- [ ] #3 The 4 gitleaks-only rules each have a recorded decision
<!-- AC:END -->
