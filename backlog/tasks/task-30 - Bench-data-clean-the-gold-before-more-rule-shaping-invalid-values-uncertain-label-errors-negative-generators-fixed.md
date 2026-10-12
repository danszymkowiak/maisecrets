---
id: TASK-30
title: >-
  Bench data: clean the gold before more rule shaping (invalid values uncertain,
  label errors negative, generators fixed)
status: To Do
assignee: []
created_date: '2026-10-12 07:16'
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
- [ ] #1 An audit report per dataset and type: how much gold fails each candidate validity rule, masked examples, and the rules chosen from it
- [ ] #2 findocs and synthetic generate only valid values; tests check every generated positive against its type's rule
- [ ] #3 validgold applies the chosen rules (REVISION bumped); the manifest counts uncertain gold per dataset and type
- [ ] #4 bench/gold_exceptions.json exists with its schema, applied at setup, a test refuses a stale entry and an entry without a rationale
- [ ] #5 A new baseline run recorded in docs/BENCHMARK.md, compared with 20261012-085837
<!-- AC:END -->
