---
id: TASK-11.19
title: 'bench: a synthetic tool-output dataset and a perturbation suite'
status: To Do
assignee: []
created_date: '2026-10-11 17:06'
labels:
  - benchmark
dependencies: []
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: high
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CredData, TAB, ai4privacy and Gretel are file and prose corpora: they hold no ANSI-coloured grep output, wrapped lines, cat -n gutters, kubectl secrets, lockfiles or encoded values, so the normaliser, decode-and-rescan and digest ideas of the report cannot be judged. A local check (report, Recall section) found a synthetic ghp_ token missed under a zero-width space, soft hyphen, fullwidth form, homoglyph, ANSI reset, CR overwrite, line wrap, base64, hex, HTML entity and markdown escape. Build a generated dataset (fixed seed, synthetic values only, nothing downloaded) in the one schema: tool-output templates (env/printenv, git diff, grep -n, cat -n, kubectl get secret -o yaml, docker config, curl -v headers, package-lock/yarn.lock/go.sum, docker images --digests) with injected secrets and PII as pos spans and digests, UUIDs, commit ids and integrity strings as neg spans; plus a perturbation table that applies each transform to the pos spans of every dataset and reports recall per transform.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 bench/setup.py builds the dataset deterministically from a seed; values come from rule-shaped generators, never from a real token; scripts/scan_tree.py stays clean
- [ ] #2 Every template has pos and neg spans with exact offsets; a test checks offsets against the text
- [ ] #3 The perturbation report lists recall per transform (zero-width, soft hyphen, NFKC-foldable, homoglyph, ANSI, CR, wrap, base64, hex, entity, escape, truncation) per dataset
- [ ] #4 Decide its role (scored or guard, TASK-11.15 rules) and record the baseline in docs/BENCHMARK.md
<!-- AC:END -->
