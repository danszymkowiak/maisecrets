---
id: TASK-62
title: >-
  redact and bench: layered architecture enforced by import-linter, adapters
  independent of each other
status: To Do
assignee: []
created_date: '2026-10-14 07:21'
updated_date: '2026-10-14 08:22'
labels:
  - redact
  - bench
dependencies:
  - TASK-17
ordinal: 123000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User, 2026-10-14: add import-linter as a dev dependency (a uv dependency group in redact/ and bench/) and refactor both packages into layers, with contracts that fail the checks. Architectural: design through a written spec first (brainstorming, then writing-plans).

Import graph measured 2026-10-14 (top-level and lazy imports):
- redact: pipeline imports nothing (the core); extract, review, models import only pipeline; rules imports paths and pipeline; paths is the one import of the plugin (maisecrets.detect), rules also imports maisecrets.regions; app imports extract, pipeline, review, rules; measure imports pipeline and lazily models, review, rules; cli imports extract and review and lazily app, models, paths. A layering of cli > app/measure > extract/models/rules/review > pipeline fits with few changes; the open points are the lazy imports in cli and measure, and whether rules, models and extract count as adapters that must not import each other.
- bench: the dataset adapters (adapters.*) import only labels, paths, schema, split, except adapters.findocs, which imports adapters.synthetic, so independence needs that shared part moved down a layer. Lower layers import upward lazily: schema and labels import detector, filters imports detector and learned, so those cycles need breaking. run, round, mutate and setup are the top (commands).
- The bench's top-level scripts (bench/run.py and the others) and tests are outside the package and are not covered by the contracts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 import-linter is a dev dependency of redact and bench, and lint-imports runs in the git hooks and the checks list of CLAUDE.md
- [ ] #2 A layers contract for each package passes, with no ignore_imports beyond ones named and justified in the spec
- [ ] #3 An independence contract over bench's adapters.* (and redact's adapter modules, as the spec defines them) passes
- [ ] #4 Every test of both packages and the bench's numbers are unchanged by the refactor
- [ ] #5 docs/REPO-STANDARDS.md (or the spec it links) describes the layers
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blocked 2026-10-14 (unattended run): needs the user's choice of layering before the spec (inbox TASK-17). Proposal in the inbox comment. No code or spec written yet.
<!-- SECTION:NOTES:END -->
