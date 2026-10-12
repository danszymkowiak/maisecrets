---
id: TASK-40
title: 'Plugin: credit-card without its context gate, generic-api-key entropy 3.3'
status: To Do
assignee: []
created_date: '2026-10-12 20:49'
labels:
  - plugin
dependencies:
  - TASK-17
priority: medium
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-21.9 (operating points): judged together on baseline 20261012-194832 (bench/mutations/round5/operating-points.toml, run 20261012-224916): accepted, CARD +325 finds (critical tier, a gap narrowed), SECRET_GENERIC +259, US_BANK_NUMBER +12; 167 more false positives (CreditCard: a Luhn-valid 13-19 digit number without a card word; generic-api-key: lower-entropy values after a key label). Real use: card numbers in exports and statements often stand without a card word (a CSV column), and a lower entropy bar keeps short or patterned API keys. Waits for the user's approval (TASK-17).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 credit-card loads without require_context; generic-api-key's entropy is 3.3; tests for both
- [ ] #2 Unit tests, replay_can_fail and the bench pass
<!-- AC:END -->
