---
id: TASK-27
title: 'Detector: build the rule set from explicit settings and pass it to scan()'
status: To Do
assignee: []
created_date: '2026-10-12 05:42'
labels:
  - refactor
  - detection
  - bench
dependencies: []
references:
  - maisecrets/detect.py
  - bench/maisecrets_bench/mutation.py
  - bench/maisecrets_bench/run.py
priority: medium
ordinal: 1200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The bench and the tests change detection by setting module globals: detect._RULES, detect.NORMALISE and now detect.SECRET_RULES, and must reset each by hand. A forgotten reset leaks one configuration into the next test or bench arm, and comparing two rule sets (TASK-19.3) means juggling them. A frozen settings value (regions, label languages, vendored secret set, normaliser stages) builds an immutable rule set; scan() takes it (default: the one built from the config, cached as today), and the bench builds one per arm. Functional core: no global the caller must restore.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 scan() and the hooks take a rule set; the default path loads it from the config once, as today
- [ ] #2 The bench and tests no longer assign detect._RULES, NORMALISE or SECRET_RULES; a grep test keeps it so
- [ ] #3 Load time and first-scan time in the hook interpreter are no worse than before (measured)
<!-- AC:END -->
