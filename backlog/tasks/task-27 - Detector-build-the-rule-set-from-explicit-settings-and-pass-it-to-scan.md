---
id: TASK-27
title: 'Detector: build the rule set from explicit settings and pass it to scan()'
status: Done
assignee: []
created_date: '2026-10-12 05:42'
updated_date: '2026-10-12 09:23'
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
- [x] #1 scan() and the hooks take a rule set; the default path loads it from the config once, as today
- [x] #2 The bench and tests no longer assign detect._RULES, NORMALISE or SECRET_RULES; a grep test keeps it so
- [x] #3 Load time and first-scan time in the hook interpreter are no worse than before (measured)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.Settings (regions, label languages, vendored secret set, normaliser stages) builds an immutable detect.RuleSet (build()); scan(text, ruleset=...) runs it, else default_ruleset() (built once from settings_from_config(): the config's regions and languages, SECRET_RULES, NORMALISE); rules() returns the default set's tuple. The _RULES cache is gone. Tests build their own sets (Swiss, Betterleaks, label languages, regions, normaliser) instead of patching active_regions and resetting globals; bench: mutation.ruleset(m, base) returns the mutated rules with their normaliser stages (apply no longer sets detect.NORMALISE), run workers keep it in run._RULESET. tests/test_ruleset.py has a grep test: no file in tests/, bench/ or scripts/ assigns detect._RULES, NORMALISE or SECRET_RULES. Same results: 1193 unit tests OK, 108/108 beliefs, bench detections identical (run 20261012-110134 against 20261012-104218, 503,733), the Swiss mutation still accepted. Timing in /usr/bin/python3, alternating old and new 3x15 runs: rule load 13.1 vs 13.2 ms, first scan 15.5 vs 15.6 ms, import 30-40 ms for both (noise).
<!-- SECTION:FINAL_SUMMARY:END -->
