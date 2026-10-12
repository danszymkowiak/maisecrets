---
id: TASK-23
title: 'Plugin: a US phone number in the (NXX) NXX-XXXX form is missed (test first)'
status: Done
assignee: []
created_date: '2026-10-11 23:25'
updated_date: '2026-10-12 12:00'
labels:
  - plugin
  - benchmark
dependencies:
  - TASK-21.8
  - TASK-30
priority: medium
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found by the findocs dataset (TASK-11.37, run 20261012-011327): every US phone of the f1099 and invoice_en templates, written '(494) 360-7563' after 'Questions:' or a comma, is missed (600 of 600), while Swiss '+41 44 ...' numbers are found. Check the phone rule's regex and context gate on this form; Nemotron's PHONE recall is 23% too. A rule change: phase 3 (after the new metrics), judged by TASK-21.8's verdict.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A unit test with a (NXX) NXX-XXXX number in prose goes red first, then green
- [x] #2 findocs and Nemotron PHONE recall before and after; no floor broken, weighted FP/1k not higher (TASK-21.8)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-10-12: rule written test first (us-phone-paren, region us, (NXX) NXX-XXXX with area code and exchange starting 2-9; a reserved middle-9 area code still counts because findocs writes (494)). Bench run 20261012-090906 against 20261012-085837: findocs PHONE 600 -> 1200 of 1200, Gretel +307 TP / +22 FP, Nemotron +1994 TP / +17 FP, ai4privacy +1 FP. Paused by the user's decision to clean the bench data first (TASK-30): the FP rise cannot be judged on uncleaned gold, and the middle-9 choice should follow the cleaned findocs generator. Work in git stash 'wip TASK-23 us-phone-paren rule'.

2026-10-12 (after TASK-30/31): rule excludes reserved middle-9 area codes now that the bench counts them as invalid gold. Run 20261012-101259: verdict accepted, PHONE recall up (findocs 100%, Gretel 63.3%, Nemotron 29.7%), weighted FP/1k 0.2912 -> 0.2921: the 43 new hits are mostly unlabelled real-looking numbers. AC #2 ('not higher') contradicts the accepted verdict: inbox question. Work in git stash 'wip TASK-23 us-phone-paren (clean gold ...)'.

2026-10-12: user accepted (inbox TASK-17). Resume from the stash.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
detect.REGIONAL_RULES: us-phone-paren (region us), (NXX) NXX-XXXX with area code and exchange starting 2-9 and no reserved middle 9 in the area code (the bench counts those as invalid gold since TASK-30). tests/test_us_phone.py red first (now on an explicit rule set, TASK-27). Bench run 20261012-135603 against 20261012-131230: PHONE findocs 80.0% -> 100%, Gretel 56.7% -> 63.3%, Nemotron 23.2% -> 29.7%; false hits +40, mostly unlabelled real-looking numbers; TASK-21.8 verdict accepted; the user accepted the trade on 2026-10-12 (inbox TASK-17), so AC #2's 'not higher' is waived by that decision.
<!-- SECTION:FINAL_SUMMARY:END -->
