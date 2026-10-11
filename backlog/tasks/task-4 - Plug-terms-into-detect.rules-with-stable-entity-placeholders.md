---
id: TASK-4
title: Plug terms into detect.rules() with stable entity placeholders
status: Done
assignee: []
created_date: '2026-10-11 07:00'
updated_date: '2026-10-11 08:23'
labels:
  - terms
  - integration
dependencies:
  - TASK-3
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
New loader beside the existing ones in maisecrets/detect.py rules(); placeholder per entity label (e.g. PERSON_A) consistent across documents and sessions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A term in a prompt is blocked/rewritten, in a tool result redacted, in a tool call input rehydrated per existing policy
- [x] #2 Same entity always maps to the same placeholder
- [x] #3 No terms.txt -> behaviour identical to upstream (all existing tests green)
- [x] #4 Integration test through the hook entry points with a temp home (tests/_isolate.py)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Paused 2026-10-11 for a client reload. Work is in stash 'wip TASK-4' (git stash list). Done: detect.scan() appends term matches after all rules (skips taken spans and runs inside ⟦…⟧), reserved labels = rule types + ENTITY_OF_TYPE + SECRET/HIDDEN; terms.TermsError is a ConfigError (hooks fail closed); vault: Entry.term, _put_term derives LABEL_c0 with metadata only (no backend value, 100y TTL, not renewed by _touch, not in live_fingerprints), get() reads the canonical from terms.txt at the call; detect falls back to no terms when terms.py is absent (standalone skill zip). tests/test_terms_hooks.py (10 tests) green; full suite 1096 OK; replay_can_fail 103/103; scan_tree, derived_counts (TESTING.md -> 1096), lint_plugin, ruff green. OPEN: python3 harness/run.py reported 'failures: 2' - not yet looked at which scenarios; check whether they fail on main too before calling this done.

Harness 'failures: 2' = plugin_folder_moved_guarded (2 checks); fails identically on clean main (2.1.296): pre-existing, environment-dependent, filed as TASK-12.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.scan() adds personal-term matches after every rule (a shape keeps its span; nothing inside a placeholder). Each entity gets the fixed placeholder LABEL_c0 in every document and session; the vault keeps only metadata for it (no value, not hunted, not renewed) and resolves it from the first plain variant in terms.txt at call time, only in a session that saw it. A bad terms.txt raises a ConfigError: hooks fail closed. Without terms.txt, behaviour is unchanged. tests/test_terms_hooks.py (10 tests) covers prompt block, result redaction, call rehydration, session scoping, no leak into store/index/audit, fail-closed. Checks: 1096 tests OK, replay 103/103, scan_tree, derived_counts, lint_plugin, ruff green; harness only fails plugin_folder_moved_guarded, which also fails on main (TASK-12).
<!-- SECTION:FINAL_SUMMARY:END -->
