---
id: TASK-19.3
title: 'Bench: Betterleaks against gitleaks, and what to do about tokenRatio'
status: To Do
assignee: []
created_date: '2026-10-11 21:31'
updated_date: '2026-10-12 10:18'
labels:
  - benchmark
  - false-positive
dependencies:
  - TASK-19.2
  - TASK-30
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From TASK-19.2 (2026-10-12): with Betterleaks on and generic-password / generic-credential-uri off, 3 unit tests lose a find: Betterleaks' generic-api-key has no password keyword, so 'password: <value>' after another label on the same line, or after a blank line, is missed (tests/test_core.py test_a_value_after_a_blank_line_is_found_in_long_text_too, tests/test_detect_rules.py test_the_label_decides_only_right_before_the_value). Bench both ways: generic-password on (with the detect-secrets fixes attached through overrides.txt) or a password keyword for generic-api-key.
<!-- SECTION:NOTES:END -->
