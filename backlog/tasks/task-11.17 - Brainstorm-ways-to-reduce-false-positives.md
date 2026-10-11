---
id: TASK-11.17
title: Brainstorm ways to reduce false positives
status: Done
assignee: []
created_date: '2026-10-11 15:46'
updated_date: '2026-10-11 17:44'
labels:
  - benchmark
  - design
dependencies: []
parent_task_id: TASK-11
priority: medium
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Requested by the user 2026-10-11. Most of the lost score is false alarms: Gretel precision 75.1% (us-bank alone ~4,000 FPs), CredData 78.6%. Brainstorm approaches beyond dropping single rules, with the bench to measure each: tighter context windows and context words per rule, paired changes (drop a rule and tighten its neighbour so the finds come back), checksums or validators (routing ABA, IBAN, Luhn) where a rule lacks one, entropy thresholds (bench/curves.py), shape filters for prose and code words, and which false alarms are acceptable for a redaction tool. Use bench/round.py brief and bench/errors.py (masked) as input; the outcome is a ranked list of candidate changes as backlog tasks or mutation files.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A written list of approaches, each with the false alarms it targets (rule, count on dev) and its risk to recall
- [x] #2 The most promising become backlog tasks or bench/mutations files, judged with bench/round.py judge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Spike findings 2026-10-11 (run 20261011-173619, probes print counts and masked shapes only; a few synthetic ai4privacy samples read with the user's OK).

Family A, number rules (Gretel): Presidio validates aba-routing, it-fiscal-code, it-vat-code, se-personnummer; the port does not (detect.PRESIDIO_VALIDATOR). Bench checksums (maisecrets_bench/validators.py; vectors: ABA 011000015, CF RSSMRA85T10A562S, personnummer 811218-9876). Share of today's hits passing: aba#0 TP 40/362, FP 40/185 (Gretel's routing numbers are generated and mostly fail: not testable here, right in real use); it-fiscal TP 3/3, FP 5/203; it-vat (Luhn) TP 0/3, FP 2/175; se#0 TP 16/18, FP 8/124; se#1 TP 0/11. Context words too generic: us-passport (us, united, states, travel, document), us-bank (check, save, debit), us-license#1 (identification, permit, lic). us-bank: 1,000+ of 2,798 dev FPs follow a SWIFT MT tag (:20:, :28C:, ...). Mutations in bench/mutations/round2/ (aba-checksum, it-checksums, se-checksum, us-passport-context, us-license-context, us-bank-context, us-bank-swift, us-bank-swift-near, checksums-and-context).

Family B, keyword rules (CredData): FPs are spread (193 of 307 files with a judged hit have one; leaving out the 20 noisiest files only lifts P 78.6 -> 85.1, capping per file lowers it). By value shape (all splits, FP/TP): identifiers 'UPPER-UPPER-..._' 375/0 on every dataset; 'UPPER_lower...' 765 FP for 1 CredData TP and 12 ai4privacy TP; digits:word on ds-keyword-colon 33/0 (ai4privacy -4). Value classes with low precision on ds-keyword-equal-signs: has-brackets 56/4, template 6/0, path-ish 51/16. Mutations b-*.toml use a new bench field allow (regexes on the value).

Family C, ai4privacy email/ip/phone 'FPs' are label gaps, not rule errors: only ~18 of 3,600 dev cases have a raw mask entry for the value. (1) ai4privacy's own chunking: the value at offset 0 of a continuation record (ids ...B, ...C) is unlabelled: email 1,005, ip 318, phone 20. (2) text the generator wrote around the injected PII (filler phones such as +1-234-567-8901, emails and IPs in obvious slots). Scorer option: do not count a detection at offset 0 of a continuation record; (2) cannot be split from real FPs without reading text, so ai4privacy precision is a lower bound.

Verdicts (bench/round.py judge, round 2, 2026-10-11): within tolerance: us-bank near word + SWIFT (+1.10/+1.15, no better than near alone), us-bank SWIFT only (+0.28/+0.29), se-personnummer Luhn (+0.03/+0.05). Strict: b-upper-dash-identifier (+0.39 dev, +0.00 check), b-digits-colon-word (+0.03/+0.00). Rejected: us-bank account words only (Gretel recall -0.41), it checksums (it-vat Luhn loses its 3 generated finds), us-passport / us-license#1 context (ai4privacy score -0.01), aba checksum (generated gold fails), b-upper-underscore-identifier (+0.82 dev, ai4privacy score -0.01), combined checksums+context. Plugin tasks: TASK-11.28 (us-bank), 11.29 (se/it checksums), 11.30 (identifier filters), 11.31 (uk-postcode), all waiting for approval in TASK-17. Questions in TASK-17: the tolerance's score rule, the ai4privacy chunk-start scorer fix.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Spike done: three families of false alarms measured with counts and masked shapes. Number rules: missing Presidio checksums and too-general context words; us-bank near-word is the big win (+1.10/+1.15). Keyword rules: identifier-shaped values (dev-only evidence). ai4privacy: label gaps, ~1,300 provable (chunk starts). Four plugin tasks (11.28-11.31) and three inbox questions (TASK-17). Bench gained validator, allow (bae3538) and filter (2f5ab40) fields.
<!-- SECTION:FINAL_SUMMARY:END -->
