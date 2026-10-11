---
id: TASK-16
title: 'Inbox: questions for the user'
status: To Do
assignee: []
created_date: '2026-10-11 11:06'
updated_date: '2026-10-11 13:15'
labels:
  - inbox
dependencies: []
priority: high
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Questions from the unattended run. Answer in a comment here, then mark this task Done; every task waiting on it becomes ready again.
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-10-11 11:06
---
TASK-11.1: please review docs/BENCHMARK.md (the decisions from the brainstorm: no folds, one dev/check split for the agent loop only; FP only when a detection touches no gold-sensitive span; CredData unlabelled lines as a separate unreviewed rate; TAB annotators by union, scored for precision only; regions per sample language; inclusion = precision and recall >= baseline on every dataset). Options: (a) approve as is; (b) change a decision. I recommend (a); the build continues on it per your instruction, and a change later only touches the scorer (TASK-11.9/11.10).
---

created: 2026-10-11 11:41
---
TASK-11.6: ai4privacy pii-masking-300k is licensed for academic and non-commercial use only (LICENSE.md: 'Access ... exclusively for academic research and non-commercial purposes'; redistribution or derivative works need a written licence from licensing@ai4privacy.com; the data is watermarked). maisecrets is published by a company (mcpgate.de), so tuning its rules with this data, and the parquet conversion, may fall outside the licence. Options: (a) drop ai4privacy and rely on Gretel (Apache-2.0, finance PII, 6 languages) for PII; (b) keep it for your own local, non-commercial measurement only, never in recommendations sent upstream; (c) ask AI4Privacy for a licence first. I recommend (a) because Gretel covers the same in-scope types (email, phone, IP, password, IBAN, card) under a clear licence, and the owner must be able to run the bench without a licence question. Found so far (40k records, no values read): in scope would be EMAIL, TEL->PHONE, IP, PASS->SECRET; the ID-like labels are random digit/letter runs, so out of scope.
---

created: 2026-10-11 12:23
---
TASK-11.15 (your question: are the datasets even useful?). Full run 2026-10-11, 30 probes (drop each of the 30 most-firing rules, rescore):
- creddata: 15,753 in-scope positives (100%), score 70.4% (P 78.6, R 63.8), 34 rules fire (21 only here), 11 of 30 probes move it. KEEP.
- gretel: 34,919 in-scope positives (9.6% of its labels), score 68.6% (P 75.1, R 63.1), 55 rules fire (40 only here), 26 of 30 probes move it. KEEP.
- tab: 0 in-scope positives, 99.7% of 1,268 documents without a false alarm (4 FPs in 9.6 M chars), 3 rules fire, 2 of 30 probes move it. DROP CANDIDATE: saturated and out of scope; it can only show a regression in legal prose.
- Overlap: creddata/gretel move the same way on 16.7% of probes: not redundant.
Options: (a) drop TAB from the score, keep it as a regression guard (a change must not lower its clean rate; it gets no weight in the mean); (b) drop it entirely; (c) keep it with equal weight. I recommend (a) because it costs 1 s per run and catches false alarms in long prose, which neither other dataset has, but with equal weight its 99.7% would dilute every real improvement to a third. ai4privacy is still parked on its licence (TASK-11.6).
---

created: 2026-10-11 12:29
---
TASK-11.10 result for you to weigh (bench/mutations/*.toml, judged 2026-10-11 with TAB as guard): your rule 'equal or better on every dataset' accepts only 'drop uk-postcode' (+0.39 on Gretel). 'Drop us-bank' is the big trade-off: Gretel false alarms 7,260 -> 3,218 (precision 75.1% -> 87.1%) but 215 fewer finds (recall 63.13% -> 62.52%), because us-bank also hits real routing/card numbers; mean score +2.09. Options: (a) keep the strict rule, and look for a combined change that recovers those 215 finds (for example drop us-bank and tighten the routing-number rule); (b) allow a small recall loss when precision gains much more (a tolerance, e.g. F1 must rise and recall may fall by at most 0.5 points). I recommend (a) first: the agent loop (TASK-11.13) can search for such pairs, and a tolerance can still come later.
---

created: 2026-10-11 12:50
---
TASK-11.14: what should the owner receive? The bench writes four markdown files that hold counts, rule ids, shapes and common words only: report.md (baseline per dataset/type/rule), usefulness.md (keep/drop per dataset), mutations report.md (each rule change accepted/rejected, ranked), errors-dev.md (FPs by rule, misses by type). Options: (a) one combined 'recommendations' markdown per round (accepted mutations with their per-dataset deltas and a few example shapes, never-fired rules, dataset verdicts), ready to paste into a GitHub issue; (b) send the four files as they are; (c) a pull request with the accepted rule changes plus the report. I recommend (a) for the first contact, because one page with the result and how to reproduce it is easier to act on than four files, and (c) once you and the owner agree on a change. The fresh-clone check passed (tests, setup of TAB from GitHub, run, usefulness, mutate, errors in a temp dir).
---

created: 2026-10-11 13:02
---
TASK-14 (flaky test): not reproduced in 7 full runs (4 suites in parallel; 3 runs of the real pre-commit hook in parallel with a bench run as load). The pre-commit and pre-push hooks now keep the test output in .git/maisecrets-pre-commit-tests.log / maisecrets-pre-push-tests.log and print the FAIL lines on failure. Options: (a) leave TASK-14 open and waiting; when a hook fails again, the log names the test and I fix it then; (b) close it as not reproducible. I recommend (a): two failures in one day are real, and the next one now costs nothing to diagnose. Mark this inbox Done to let it run again, or tell me to close it.
---

created: 2026-10-11 13:06
---
TASK-8: the draft feature request for upstream (personal terms + PDF/image ask) is in TASK-8's notes. Options: (a) approve it as is, and I file it with /maisecrets:report feature (it prints a prefilled GitHub link; you open it and submit); (b) edit it first; (c) wait until the benchmark recommendations are ready and send both together. I recommend (c) because one contact with two concrete, tested contributions is likelier to get an answer than two separate requests; filing stays your click either way.
---

created: 2026-10-11 13:15
---
TASK-15 (false alarm on a keyword, a colon and prose): a narrow fix works: in ds-keyword rules, skip a letters-only lowercase value directly followed by a space and a joining word (and, or, of, the, und, oder, ...). Benchmark: 5 fewer false alarms of ds-keyword-colon (733 -> 728), no true positive lost on CredData, Gretel or TAB. But it contradicts a deliberate true positive in tests/fp_corpus.py: 'label+random after value word' (a password label, the word 'identifier', then 'and the token is ...') must stay a hit. Options: (a) take the fix and turn that corpus case into a NO_HIT (a plain word followed by 'and' is prose); (b) keep upstream's decision and close TASK-15 as 'keep the false alarm'; (c) a narrower fix that only skips inside a markdown table cell or after a plural label word ('secrets:', 'passwords:'). I recommend (c): it removes the case that happened without overruling the upstream decision; the benchmark can measure it the same way. The work is in stash 'wip TASK-15'.
---
<!-- COMMENTS:END -->
