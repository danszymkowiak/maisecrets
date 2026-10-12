---
id: TASK-28
title: >-
  Bench: run Swiss-locale samples with region ch, and enough AHV positives for
  the 0.999 floor
status: Done
assignee: []
created_date: '2026-10-12 06:27'
updated_date: '2026-10-12 09:34'
labels:
  - bench
dependencies:
  - TASK-30
references:
  - bench/maisecrets_bench/run.py
  - bench/maisecrets_bench/adapters/findocs.py
priority: medium
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-20 added the Swiss rules (region ch) and judged them as a mutation that runs them in every group. A plain bench run still groups samples by language only (run.py LANGUAGES: de -> [de], fr -> []), so findocs' de_CH and fr_CH documents never run the ch rules and CH_AHV/CH_UID show as gaps in every baseline. Group by locale tag where a sample has one (locale:de_CH -> regions [ch], labels de/fr/it), or another way that keeps the other datasets' groups unchanged. findocs also has 900 AHV positives; the critical floor (0.999) needs about 3,000 with no miss to be shown (Wilson bound): raise the Swiss templates' count.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A plain bench run runs the ch rules on findocs' Swiss documents and on no other dataset's group unless its locale is Swiss
- [x] #2 findocs has at least 3,000 valid AHV positives; CH_AHV's floor status is clears or fails, not too_few
- [x] #3 A new baseline is recorded in docs/BENCHMARK.md
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
run.LOCALES and run.group_of: a sample tagged locale:de_CH/fr_CH/it_CH runs in its own group (de:de_CH) with region ch; every other sample keeps its language group (test in bench/tests/test_run.py, LocaleGroupTests). findocs repeats its three AHV templates four times (REPEAT): 6,000 documents, 3,600 AHV and 2,400 UID positives, all valid (test_findocs). Baseline 20261012-112723: CH_AHV 3600/3600 clears (lower bound 0.99925), CH_UID 2400/2400 clears; groups as intended; no false positive moved. docs/BENCHMARK.md (Regions) updated.
<!-- SECTION:FINAL_SUMMARY:END -->
