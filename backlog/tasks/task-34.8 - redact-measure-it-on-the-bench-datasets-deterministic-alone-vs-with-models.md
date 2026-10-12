---
id: TASK-34.8
title: 'redact: measure it on the bench datasets (deterministic alone vs with models)'
status: Done
assignee: []
created_date: '2026-10-12 10:06'
updated_date: '2026-10-12 17:44'
labels:
  - redact
  - bench
dependencies:
  - TASK-34.5
parent_task_id: TASK-34
priority: medium
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The bench (bench/, TASK-30 clean gold) already labels names and addresses, which the plugin does not detect. Run the tool's detection over findocs, Gretel, Nemotron and Mendeley: recall and false positives per type for the deterministic pass alone, each model alone, and the vote; time per document on CPU. The spec notes that published model scores do not transfer to German financial and legal prose: this answers it on our own data. Licence rules of the bench apply (ai4privacy stays local).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A report per configuration (deterministic, each model, vote) with recall and false positives per type and time per document
- [x] #2 docs/REDACT.md records the default model set chosen from it
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: the model extra installed and each backend checked on the real libraries: urchade needed sentencepiece+protobuf (added), openai/privacy-filter answered word pieces (merge_pieces), gliner2 backend written for fastino (local class only; asked in its own labels). Measurement: python -m maisecrets_redact.measure (redact/maisecrets_redact/measure.py), 150 dev samples per dataset (findocs, gretel, nemotron, mendeley), 6 detectors; run 20261012-161906 under ~/.cache/maisecrets-bench/redact/. User 2026-10-12: models only in this tool, never the plugin.

Follow-up (user, 2026-10-12): models now read the text after the rules (ba3b74a); privacy-filter's private_date mapped (its 0 % birth dates was a mapping bug); defaults knowledgator + fastino + privacy-filter, chosen by least overlapping misses (8f7d26b; correlation table in docs/REDACT.md). Re-measured rules-first: run 20261012-191234. Report for the user: https://claude.ai/code/artifact/b7c326ff-8386-44c0-b6f3-b713799fa4cf. Vote rule: inbox TASK-17.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Measured with redact/maisecrets_redact/measure.py (run 20261012-161906, 600 documents, re-scored on the relabelled findocs). The rules hide almost no names or addresses; each model adds 66-87 % of names. Defaults now urchade, knowledgator and fastino (gliner2 backend written); openai/privacy-filter dropped (no date of birth found, twice the time). docs/REDACT.md has the table. Open for the user (TASK-17): a two-of-three vote instead of unanimity.
<!-- SECTION:FINAL_SUMMARY:END -->
