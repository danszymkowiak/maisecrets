---
id: TASK-11.25
title: 'Experiment: a normaliser with an offset map before the shape rules'
status: In Progress
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-12 12:45'
labels:
  - benchmark
dependencies:
  - TASK-11.19
  - TASK-19.7
references:
  - reports/Deterministic redaction detection ideas.md
parent_task_id: TASK-11
priority: high
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Report rank 1 for recall (the strongest measured gap). One function returns a normalised copy of the text and an index map back to the original, so spans found in the copy redact the true text: strip ANSI/OSC and render CR overwrites; delete zero-width, soft hyphen and bidi format characters (fast path when text.isascii()); strip cat -n, grep and diff gutters; then decode HTML entities and escapes; NFKC fullwidth folding last, shape rules only (notes disagree on its value). Guarded line unwrap (join only when the joined text hits a prefix-anchored rule that neither half hits) is a separate variant, because the README records that a plain next-line join failed on .env files. The C25 term matcher needs the same function (TERMS.md). This is a plugin change behind a switch, measured on the synthetic dataset and the perturbation suite.

Phase 4 (user, 2026-10-12): mutations and rule ideas run last, after the new datasets (TASK-11.33, 11.34, 11.35, 11.37), the new metrics (TASK-21: recall floors per type on valid gold, then weighted false positives per 1,000 tokens; verdict in TASK-21.8) and the new rule set (TASK-19, re-baselined in TASK-19.7). Judge by TASK-21.8's verdict; the old strict/within-tolerance verdict and the mean score change appear only as a comparison. Numbers quoted above come from the blended score and the gitleaks rules of 2026-10-11: re-measure before relying on them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Recall per transform before and after, on the perturbation suite, for each normaliser stage
- [ ] #2 Judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens): no floor broken, no gap worse, weighted FP/1k not higher; added hook time on 25 KB and 120 KB synthetic input reported
- [ ] #3 The guarded-unwrap variant judged separately against .env-shaped neg spans
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12, tooling in f843f66: maisecrets/normalise.py (stages ansi, cr, invisible, gutter, entity, escape, fullwidth; a Normalised object with span() back to the original; a lone CR is deleted, not rendered, because rendering hides half a value the model still reads), detect.NORMALISE (empty: off), tests/test_normalise.py; bench op = "normalise" in mutations, perturb.py --mutation, and one mutation per stage plus all in bench/mutations/round4/. Nothing judged. Rough timing with every stage on (taken while a judge ran, so high): 25 KB plain +6 ms, 25 KB with ANSI colour +179 ms, 120 KB plain +135 ms, 120 KB ANSI +519 ms. A changed text is scanned twice in full; scanning only the changed lines is the obvious speed-up if the stages pass. Guarded unwrap (AC 3) not built.

2026-10-12, run 3: (1) the 8 normaliser mutations (bench/mutations/round4/) are being judged against baseline 20261012-141549 in the background; result lands in ~/.cache/maisecrets-bench/mutations/<newest>/ (started about 14:24). (2) AC 3: maisecrets/unwrap.py (guarded unwrap: a break between token characters is removed only when a SECRET shape rule finds a token across it that the line before does not hold whole) with tests/test_unwrap.py (wrapped token joined and mapped back to both lines; .env lines, a whole token followed by a word, and prose stay apart). Not yet wired in as a normaliser stage, not yet benched (needs a mutation once wired, plus the .env-shaped negatives check). Still to do: perturbation recall per stage (bench/perturb.py --mutation <stage>.toml), hook time on 25 KB and 120 KB, record all in docs/BENCHMARK.md. Do not edit maisecrets/ while a bench run is going (workers import the detector fresh).
<!-- SECTION:NOTES:END -->
