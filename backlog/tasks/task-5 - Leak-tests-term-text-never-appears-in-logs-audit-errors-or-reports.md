---
id: TASK-5
title: 'Leak tests: term text never appears in logs, audit, errors or reports'
status: Done
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-11 08:48'
labels:
  - terms
  - security
  - tdd
dependencies:
  - TASK-4
priority: high
ordinal: 5000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Audit log, events, incident records, /maisecrets:report text and every error path contain the placeholder or line number, never a term
- [x] #2 /maisecrets:list and status show counts/labels only
- [x] #3 scripts/scan_tree.py still clean
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tests/test_terms_leaks.py (8 tests) drives a prompt, a tool result and a resolving tool call with terms through hooks.main, a hook crash with a term in the payload, and every loader refusal; then searches the hook answers, every home file but terms.txt (audit, events, hooks.log, index, incident record) and the output of list, status, audit, report, report last/1, scan. No leak found in existing code. New: status prints 'terms: N entities (LABELS)', 'terms: none' or 'terms: unusable (<file: line n: reason>)'. Mutations checked: a term in a loader message and the resolved term in events.log each turn the tests red. Checks: 1110 tests OK, replay 103/103, scan_tree, derived_counts, lint_plugin, ruff green.
<!-- SECTION:FINAL_SUMMARY:END -->
