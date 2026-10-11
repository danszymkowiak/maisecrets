---
id: TASK-11.34
title: 'Bench: Nemotron-PII adapter'
status: To Do
assignee: []
created_date: '2026-10-11 21:40'
labels:
  - benchmark
  - dataset
dependencies: []
references:
  - 'https://huggingface.co/datasets/nvidia/Nemotron-PII'
parent_task_id: TASK-11
priority: high
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
nvidia/Nemotron-PII (Hugging Face, CC-BY-4.0, not gated): 100k train and 100k test records, 50+ industries, 55+ PII/PHI types, English only. Columns: uid, domain, document_type, document_format (structured or unstructured, about half each), locale (us 50k, intl 50k), text, spans. Covers the US tax side (SSNs, account numbers). A label table bench/labels/nemotron.toml maps every label to a maisecrets type or OUT_OF_SCOPE. Personal, local use (user, 2026-10-11): a licence only needs to allow the user's own non-commercial measurement; the data still never enters the repository (docs/BENCHMARK.md, Hygiene) and a report that goes elsewhere leaves it out.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The adapter writes the common schema with a fixed dev/check split by uid; the label table maps every label in the data
- [ ] #2 Scores are reported by locale (us, intl) and by document_format
- [ ] #3 docs/BENCHMARK.md has the dataset in its table, with its licence and role (scored or guard), decided after the usefulness check
<!-- AC:END -->
