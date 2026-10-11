---
id: TASK-11.34
title: 'Bench: Nemotron-PII adapter'
status: Done
assignee: []
created_date: '2026-10-11 21:40'
updated_date: '2026-10-11 23:31'
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
nvidia/Nemotron-PII (Hugging Face, CC-BY-4.0, not gated): 100k train and 100k test records, 50+ industries, 55+ PII/PHI types, English only. Columns: uid, domain, document_type, document_format (structured or unstructured, about half each), locale (us 50k, intl 50k), text, spans. Covers the US tax side (SSNs, account numbers). A label table bench/labels/nemotron.toml maps every label to a maisecrets type or OUT_OF_SCOPE. The fork is public and anyone may run the bench (user, 2026-10-11), so the licence must hold for any user, not only the owner. A dataset whose terms restrict use (non-commercial, competition-only, no derivatives, an account to accept terms) is opt-in like ai4privacy: a setup flag, off by default, its terms named in bench/README.md, and the person running it accepts them. The data and anything derived from it never enter the repository (docs/BENCHMARK.md, Hygiene).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The adapter writes the common schema with a fixed dev/check split by uid; the label table maps every label in the data
- [x] #2 Scores are reported by locale (us, intl) and by document_format
- [x] #3 docs/BENCHMARK.md has the dataset in its table, with its licence and role (scored or guard), decided after the usefulness check
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Adapter bench/maisecrets_bench/adapters/nemotron.py and table bench/labels/nemotron.toml (all 55 labels; in scope: email, phone and fax, ipv4/6, card, password, api_key, ssn, ABA, account number; tax_id, http_cookie, national_id and the rest out of scope, reasons in the table). Test split only (100,000), pinned revision, CC BY 4.0, default in setup. Sample id locale:uid, group and split by uid (every uid has a us and an intl record; a first run collided them); schema.write refuses repeated sample ids. Tags locale:* and format:* scored apart. Baseline 20261012-012544: P 99.1%, R 63.5%, F1 77.4%; cards 11.7%, phones 23.1%, secrets 21.5% are the gaps. Usefulness: keep, scored (docs/BENCHMARK.md); the user may still drop it (inbox TASK-17).
<!-- SECTION:FINAL_SUMMARY:END -->
