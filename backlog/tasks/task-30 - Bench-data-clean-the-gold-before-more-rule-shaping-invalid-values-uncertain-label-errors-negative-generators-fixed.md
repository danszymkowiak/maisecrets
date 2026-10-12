---
id: TASK-30
title: >-
  Bench data: clean the gold before more rule shaping (invalid values uncertain,
  label errors negative, generators fixed)
status: Done
assignee: []
created_date: '2026-10-12 07:16'
updated_date: '2026-10-12 07:55'
labels:
  - bench
  - data
dependencies: []
references:
  - bench/maisecrets_bench/validgold.py
  - bench/maisecrets_bench/adapters/findocs.py
priority: high
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decided 2026-10-12: clean the bench data before any further rule shaping or benchmarking. TASK-23 showed why: findocs writes US phones with a reserved area code ((494) ...), so a rule tuned to the data would accept shapes no real number has, and false-positive counts mix real false alarms with labelling problems.

Approach (proposed to the user):
1. Our generators (findocs, synthetic): fix at the source, only valid values (US phones under the numbering plan, and whatever the audit finds). The generator version changes, so setup rebuilds.
2. Third-party datasets: extend valid gold (validgold.py, TASK-21.6) with validity rules per type beyond checksums (phone plausibility per country and E.164 length, e-mail syntax, IP ranges, ...), decided from an audit, not guessed. Failing gold becomes uncertain (neither miss nor false alarm). Bump REVISION.
3. What a rule cannot catch: bench/gold_exceptions.json, reviewed entries {dataset, sample_id, start, end, label, verdict, rationale}. verdict: 'negative' where the label is wrong and the text is no personal data (a product code labelled PHONE), 'uncertain' where it is PII-shaped but invalid, 'drop' only for a broken record. Applied at setup; a test fails on an entry that no longer matches its sample's text.
Why not delete samples wholesale: they hold valid gold and negatives too. Why not label every invalid value negative: the bench would reward leaving a plausible value in the clear, and for a redaction tool a leak costs more than an over-redaction. Values are never written to the repository; exceptions name positions, the report masks values (bench/errors.py style).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An audit report per dataset and type: how much gold fails each candidate validity rule, masked examples, and the rules chosen from it
- [x] #2 findocs and synthetic generate only valid values; tests check every generated positive against its type's rule
- [x] #3 validgold applies the chosen rules (REVISION bumped); the manifest counts uncertain gold per dataset and type
- [x] #4 bench/gold_exceptions.json exists with its schema, applied at setup, a test refuses a stale entry and an entry without a rationale
- [x] #5 A new baseline run recorded in docs/BENCHMARK.md, compared with 20261012-085837
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Audit (bench/audit.py, maisecrets_bench/audit.py; run 20261012-094314): candidate validity rules for PHONE, EMAIL, IP and US_BANK_NUMBER, counts and shapes per dataset. Rules chosen from it went into validgold.py (gold valid3): phone digits, letters, repeated digit, North American plan for +1/US layouts (a leading 0 is a foreign trunk prefix, not judged); e-mail syntax and reserved domains; IP parse and public; bank digits and letters, a valid IBAN relabelled IBAN. Failing gold is uncertain; a span with nothing of its type (no digit, no @) is negative; trimming for these types takes only a whole pattern match. findocs and synthetic generate only NANP-valid phones (they had 59 and 35 reserved area codes), with a test over every generated positive. bench/gold_exceptions.json (empty) with exceptions.py: place + text hash + verdict + rationale, applied at setup, stale entries refused. New baseline 20261012-094904 recorded in docs/BENCHMARK.md: mean 79.9% to 81.4%; e-mail and IP misses were nearly all invalid gold; phone stays the gap. Follow-up TASK-31: Nemotron's valid IBANs labelled as bank numbers are missed (42 of 47).
<!-- SECTION:FINAL_SUMMARY:END -->
