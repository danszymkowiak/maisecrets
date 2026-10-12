---
id: TASK-34.4
title: >-
  redact: local PII model backends behind one interface, as an optional extra
  (test first)
status: To Do
assignee: []
created_date: '2026-10-12 10:06'
labels:
  - redact
  - tdd
dependencies:
  - TASK-34.1
parent_task_id: TASK-34
priority: high
ordinal: 90000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A detector interface (text -> spans with a type and score) with a GLiNER-class backend (the gliner library) in an optional dependency group, so the base install stays small. Models are config values, not hard-coded (spec shortlist: Fastino GLiNER2-PII, OpenAI Privacy Filter, NVIDIA GLiNER-PII for clinical text, Knowledgator GLiNER, Piiranha). Check each model's licence first: a permissive one may be a default, a restrictive one (non-commercial, no-derivatives) is opt-in with its terms named in the README (memory: public fork licensing). Models are downloaded once into a cache outside the repository and run on CPU; nothing is sent to a remote API. Long texts are chunked with overlap so a span across a chunk boundary is not lost.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tests first with a fake backend: chunking with overlap finds a span across a boundary; types map to the tool's placeholder types
- [ ] #2 Each shortlisted model's licence is recorded with its source; only permissive ones are defaults
- [ ] #3 Without the extra installed the tool runs the deterministic pass alone and says so once
<!-- AC:END -->
