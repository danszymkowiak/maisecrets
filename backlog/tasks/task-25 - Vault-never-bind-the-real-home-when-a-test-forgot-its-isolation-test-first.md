---
id: TASK-25
title: 'Vault: never bind the real home when a test forgot its isolation (test first)'
status: To Do
assignee: []
created_date: '2026-10-12 05:42'
updated_date: '2026-10-12 06:03'
labels:
  - tdd
  - safety
  - refactor
dependencies:
  - TASK-17
references:
  - maisecrets/vault.py
  - tests/_isolate.py
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
maisecrets/vault.py binds HOME, INDEX, CONFIG and SERVICE at import. On 2026-10-12 a scratch runner imported maisecrets.detect and loaded the rules (detect.active_regions imports vault.load_config) before tests/_isolate.py set MAISECRETS_HOME. The suite then ran against the real ~/.maisecrets: tests/test_vault.py _reset() deletes index.json, vault.json, vault.enc.json, key and the logs there and writes a plaintext jsonfile config.json (inbox TASK-17, comment #7). Any future runner or bench script can repeat this.

Fix, test first: (1) when MAISECRETS_TEST_HOME_OWNED is set, vault refuses a home that is not the one it names, or the default home, with a loud error before any read or write; (2) resolve the paths per call (or through one function) instead of at import, so the import order cannot pick the wrong home; check every module that reads the home (incidents.py too). Keep upstream's CI in mind: it runs as root in python:3.12-slim.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test imports maisecrets.detect and loads the rules before tests/_isolate, then runs a store write and a reset: nothing under the real home is touched (asserted with a fake HOME standing in for the user's home), and the call fails loudly
- [ ] #2 No module binds the vault home at import any more; a grep test or a belief keeps it so
- [x] #3 docs/TESTING.md says a runner must import tests/_isolate first, and why
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: guards done (vault.WrongHome/_check_home in load_config, Vault(), make_backend; the import-order check in tests/_isolate.py), tests/test_isolation_order.py, docs/TESTING.md Isolation. A first version refused any home other than the marker's: 15 tests that give a child or the vault a second temp home on purpose failed, so the vault guard refuses only the user's own ~/.maisecrets. AC #2 waits on the inbox (option a recommended: drop it).
<!-- SECTION:NOTES:END -->
