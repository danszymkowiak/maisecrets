---
id: TASK-34
title: >-
  Epic: redact, a document redaction CLI next to the plugin (deterministic rules
  + local PII models)
status: To Do
assignee: []
created_date: '2026-10-12 10:05'
updated_date: '2026-10-13 06:46'
labels:
  - epic
  - redact
dependencies:
  - TASK-34.7
references:
  - 'https://claude.ai/code/artifact/6a67afae-e26b-4364-b168-63beda199b37'
priority: high
ordinal: 86000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided with the user 2026-10-12; spec: the doc 'PDF/CSV/Excel Redaction Tool — Spec' (link in references). A separate command the user runs as data prep, before documents known to hold personal data go to Claude: extract text (PDF, CSV, Excel; one file or a whole directory), redact it with the plugin's deterministic rules plus local purpose-built PII models (GLiNER class) for what rules cannot find (names, free-form addresses), optionally reversibly.

It does NOT change the plugin: the plugin must stay fast and light, so the tool lives in its own folder (redact/, its own uv project like bench/) and imports maisecrets.detect (a RuleSet built from Settings, TASK-27); no model, no heavy library and no new dependency reaches maisecrets/ or hooks/. Models run locally, never through a remote API. Every dependency and model licence must hold for any user of the public fork; a restrictive one is opt-in (memory: public fork licensing). Out of scope (spec): OCR of scanned PDFs, rebuilding xlsx/csv files with redacted cells (output is flattened text), the post-read hook.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 redact <file> and redact <directory> produce redacted text with the deterministic rules alone, and with local models when installed
- [x] #2 The plugin (maisecrets/, hooks/) gains no dependency and no import of the tool; its tests and harness are unchanged
- [x] #3 docs/REDACT.md says what the tool does, what it never does (no network for models or data), and how to install the model extra
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-13: AC #1-#3 met by TASK-34.1-34.6 and 34.8. The epic stays open for TASK-34.7 (--reversible), which waits on the user's answer (inbox TASK-17 #14); it now depends on 34.7.
<!-- SECTION:NOTES:END -->
