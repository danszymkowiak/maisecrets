---
id: TASK-34.4
title: >-
  redact: local PII model backends behind one interface, as an optional extra
  (test first)
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 11:42'
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
- [x] #1 Tests first with a fake backend: chunking with overlap finds a span across a boundary; types map to the tool's placeholder types
- [x] #2 Each shortlisted model's licence is recorded with its source; only permissive ones are defaults
- [x] #3 Without the extra installed the tool runs the deterministic pass alone and says so once
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
redact/maisecrets_redact/models.py: Backend protocol (text -> start, end, label, score); detector_from() chunks with overlap (default 2000/200), leaves a span touching a cut edge to the neighbouring chunk, keeps a span seen twice once, maps labels to the tool's types (NAME, ADDRESS, EMAIL, PHONE, DOB, ACCOUNT, NATIONAL_ID, PASSPORT, TAX_ID) and drops unknown ones. Backends: gliner (zero-shot labels) and token-classification (transformers); gliner2 raises NotImplementedError until TASK-34.8 measures its API. Registry of 7 models with licence and Hugging Face source (read from each model's API record 2026-10-12): 5 Apache-2.0, nvidia/gliner-PII (NVIDIA Open Model License) and piiranha (CC BY-NC-ND 4.0) opt-in via --accept-model-terms (TermsNotAccepted otherwise). Defaults (provisional, TASK-34.8 settles): urchade/gliner_multi_pii-v1, knowledgator/gliner-pii-base-v1.0, openai/privacy-filter. Optional extra 'models' (torch from the CPU index, transformers, gliner) in pyproject and uv.lock; without it the command says once that only the rules run (--rules-only silences it). Tests use a fake backend; the real backends are first run in TASK-34.8.
<!-- SECTION:FINAL_SUMMARY:END -->
