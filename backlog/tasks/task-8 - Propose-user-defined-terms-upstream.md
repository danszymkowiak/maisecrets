---
id: TASK-8
title: Propose user-defined terms upstream
status: To Do
assignee: []
created_date: '2026-10-11 07:01'
updated_date: '2026-10-12 17:48'
labels:
  - upstream
dependencies:
  - TASK-17
priority: low
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
File a feature request on Mcpgate-de/maisecrets (via /maisecrets:report) so the fork can be dropped if merged. Outward-facing: confirm with the user first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 User approved the issue text before it is filed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-11 (run): the fork raised the Python floor to 3.12 (TASK-9, 2a77302) and dropped the unit_python39 job from .gitlab-ci.yml. Upstream supports 3.9 (stock macOS). A change offered upstream must leave that out: build the terms commits on upstream's main without TASK-9, and run the suite under 3.9 (uv has cpython-3.9 here; the terms code passed 1110 tests on 3.9 before TASK-9).

DRAFT issue for Mcpgate-de/maisecrets (2026-10-11, waiting for the user's approval; not filed):

Title: Feature request: user-defined personal terms (names, addresses, case numbers) redacted like secrets

Body:
maisecrets finds values by shape, so a name, an address or a case number goes to the model as typed (README, 'Names are not detected'). A fork implements a small, opt-in list of personal terms:

- ~/.maisecrets/terms.txt (mode 0600, under C8, never read into a session): one entity per line, a label and its variants separated by |, e.g. PERSON_A  Jan Kowalski | Kowalsk* | Jan. Four match modes by * at the ends (standalone word, word start, word end, anywhere), case-insensitive, any script, whitespace-tolerant; longest variant wins.
- Each entity gets one fixed placeholder (key LABEL_c0) in every document and session. The term is never copied into the store; a tool call gets the first plain variant back under the existing gates (C4, C7, C9, C16), only in a session that saw it.
- Terms run after every shape rule, through the existing paths (C1 prompt, C2 tool results, C3 transcripts, C19 subagent reports). No terms.txt: behaviour unchanged.
- A bad file fails closed (ConfigError); messages name the file and line number, never the text. /maisecrets:status shows the count and labels only.
- A Read of a PDF or an image asks first (Codex: deny), because no hook can redact a document; the deny reason and the session primer name pdftotext / tesseract, whose output passes C2.
- Proposed control C25 with five beliefs (replay_can_fail), tests for every path and a leak test over logs, audit, events, incidents and reports.

The fork's commits can be offered as a pull request against upstream main, on Python 3.9 (the fork itself moved to 3.12; that part would stay out). Would you take such a change?

2026-10-11: user chose to send this together with the bench recommendations page (TASK-11.14).

2026-10-12: approval asked in the inbox (TASK-17).
<!-- SECTION:NOTES:END -->
