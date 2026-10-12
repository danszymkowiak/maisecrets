---
id: TASK-11.25
title: 'Experiment: a normaliser with an offset map before the shape rules'
status: Done
assignee: []
created_date: '2026-10-11 17:07'
updated_date: '2026-10-12 16:46'
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
- [x] #1 Recall per transform before and after, on the perturbation suite, for each normaliser stage
- [x] #2 Judged by TASK-21.8's verdict (recall floors per type, then weighted FP per 1,000 tokens): no floor broken, no gap worse, weighted FP/1k not higher; added hook time on 25 KB and 120 KB synthetic input reported
- [x] #3 The guarded-unwrap variant judged separately against .env-shaped neg spans
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12, tooling in f843f66: maisecrets/normalise.py (stages ansi, cr, invisible, gutter, entity, escape, fullwidth; a Normalised object with span() back to the original; a lone CR is deleted, not rendered, because rendering hides half a value the model still reads), detect.NORMALISE (empty: off), tests/test_normalise.py; bench op = "normalise" in mutations, perturb.py --mutation, and one mutation per stage plus all in bench/mutations/round4/. Nothing judged. Rough timing with every stage on (taken while a judge ran, so high): 25 KB plain +6 ms, 25 KB with ANSI colour +179 ms, 120 KB plain +135 ms, 120 KB ANSI +519 ms. A changed text is scanned twice in full; scanning only the changed lines is the obvious speed-up if the stages pass. Guarded unwrap (AC 3) not built.

2026-10-12, run 3: (1) the 8 normaliser mutations (bench/mutations/round4/) are being judged against baseline 20261012-141549 in the background; result lands in ~/.cache/maisecrets-bench/mutations/<newest>/ (started about 14:24). (2) AC 3: maisecrets/unwrap.py (guarded unwrap: a break between token characters is removed only when a SECRET shape rule finds a token across it that the line before does not hold whole) with tests/test_unwrap.py (wrapped token joined and mapped back to both lines; .env lines, a whole token followed by a word, and prose stay apart). Not yet wired in as a normaliser stage, not yet benched (needs a mutation once wired, plus the .env-shaped negatives check). Still to do: perturbation recall per stage (bench/perturb.py --mutation <stage>.toml), hook time on 25 KB and 120 KB, record all in docs/BENCHMARK.md. Do not edit maisecrets/ while a bench run is going (workers import the detector fresh).

Bench result (mutation run 20261012-150659 against baseline 20261012-141549, TASK-21.8 verdict): entity accepted and clean (CredData +4 true, SECRET_PREFIXED 1634 -> 1636, no false positive anywhere). escape 'accepted' only because CARD gains 1 find, but Gretel false hits 5583 -> 5643 (+60): a bad trade by the true/false ratio the user asked for (TASK-18.2); do not switch it on. all = entity + escape costs. ansi, cr, fullwidth, gutter, invisible: neutral (the datasets hold none of those disguises); their value is for the perturbation suite to show. Next: perturb.py --mutation per stage (recall per transform), hook time on 25 KB and 120 KB, then propose switching on entity (and the neutral stages if perturbation shows gains and the time is small); escape stays off.

2026-10-12, run 4: AC 1 done (docs/BENCHMARK.md, Normaliser stages): each stage restores its transform to 88-89 % (87.8 % untouched), none changes another transform. Time (bench/normtime.py, idle): plain +0/+2 ms; a changed 25 KB text +19 ms, 120 KB +95 ms (the second full pass). unwrap wired as the last stage (07acd99); a whole value found in the copy now replaces the part the raw text found. Queued: mutate.py current-code (TASK-35 alone), normalise-unwrap, normalise-proposed (ansi cr invisible gutter entity fullwidth) against 20261012-141549, then perturb.py --mutation normalise-unwrap. Then: AC 2/3 verdicts, and the switch is an inbox question.

unwrap judged (AC 3): perturbation wrap recall 30.6 % -> 32.1 % (+141, perturb 20261012-174412, nothing else moves); .env lines stay apart (tests); but +107 ms on 25 KB and +517 ms on 120 KB of plain prose (busy machine). Stays off; cheaper guard filed as TASK-37. Dataset verdict in the queued clean run (mutate-r6).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Measured and judged: maisecrets/normalise.py stages and the guarded unwrap (maisecrets/unwrap.py, the last stage). Proposed set (ansi, cr, invisible, gutter, entity, fullwidth) accepted on clean gold, each restores its perturbation to ~88 % recall, +19 ms/+95 ms on 25/120 KB when the text changes (bench/normtime.py); escape and unwrap stay off (TASK-37 for a cheaper unwrap). docs/BENCHMARK.md, Normaliser stages. Switching on is an inbox question (TASK-17).
<!-- SECTION:FINAL_SUMMARY:END -->
