---
id: TASK-11.18
title: >-
  bench: a value filter a mutation can add to a rule, with the text around the
  value
status: Done
assignee: []
created_date: '2026-10-11 17:06'
updated_date: '2026-10-11 17:24'
labels:
  - benchmark
dependencies: []
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: high
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enables the filter experiments from the redaction-ideas report (digest shapes, entropy variants, word-likeness, label classifier). Today a mutation can only replace a rule's validator; on a ds_value rule that drops the ds_value checks and the glued-label path in detect.scan, so a new filter cannot be stacked on an existing one. Add a mutation field (e.g. filter = "bench:name") that runs after the rule's own validator and receives the value plus the text and span, so a filter can read the label before the value. Bench-only; the plugin is not edited.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A mutation can set filter = "bench:<name>" on any rule; the rule's validator, entropy and allow still apply first
- [x] #2 A filter gets (value, text, start, end) and returns keep or drop; an unknown name stops validate() like an unknown field
- [x] #3 Tests: a ds_value rule with a filter keeps its glued-label behaviour; a filter that drops everything gives zero hits for that rule
- [x] #4 docs/BENCHMARK.md and bench/README.md describe the field
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
filter = "bench:<name>" on set or add: a function of maisecrets_bench/filters.py gets (value, text, start, end) and keeps or drops the hit. The bench wraps detect._allowed per worker, so the filter runs after the rule's validator, entropy, context and allowlist and before the span is claimed. Unknown names stop validate(). Tests: glued ds_value hit kept with a keeping filter that reads the label; drop_all removes the rule's hits; validator runs first; filter on an added rule. Docs: BENCHMARK.md and bench/README.md (also validator and allow).
<!-- SECTION:FINAL_SUMMARY:END -->
